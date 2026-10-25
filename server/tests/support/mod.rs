use std::sync::Arc;
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use raicho_protocol::authentication::{authentication_message, client_proof, to_hex};
use raicho_protocol::contract_generated::Authenticate;
use raicho_server::connector::{Connector, ConnectorListener};
use raicho_server::credentials::Credential;
use raicho_server::persistence::{CredentialStore, Database};
use serde_json::{Value, json};
use tempfile::TempDir;
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::tungstenite::{
    Message, client::IntoClientRequest, handshake::client::Request,
};
use tokio_tungstenite::{MaybeTlsStream, WebSocketStream, connect_async};

pub type Socket = WebSocketStream<MaybeTlsStream<TcpStream>>;
pub const ORIGIN: &str = "moz-extension://12345678-1234-1234-1234-123456789abc";

pub struct Fixture {
    pub connector: Arc<Connector>,
    pub database: Arc<Database>,
    pub address: String,
    server: tokio::task::JoinHandle<()>,
    _directory: TempDir,
}

impl Fixture {
    pub async fn new() -> Self {
        let directory = tempfile::tempdir().unwrap();
        let database = Arc::new(Database::open(directory.path()).await.unwrap());
        CredentialStore::new(&database)
            .initialize(&Credential::parse(&"a".repeat(64)).unwrap())
            .await
            .unwrap();
        let connector = Connector::new(Arc::clone(&database));
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = format!("ws://{}/connector/v1", listener.local_addr().unwrap());
        let application = connector.router();
        let server = tokio::spawn(async move {
            axum::serve(ConnectorListener::new(listener), application)
                .await
                .unwrap()
        });
        Self {
            connector,
            database,
            address,
            server,
            _directory: directory,
        }
    }

    pub fn request(&self) -> Request {
        let mut request = self.address.clone().into_client_request().unwrap();
        request
            .headers_mut()
            .insert("Origin", ORIGIN.parse().unwrap());
        request
    }

    pub async fn connect(&self) -> (Socket, String) {
        let mut socket = connect_async(self.request()).await.unwrap().0;
        let challenge = receive(&mut socket).await;
        assert_eq!(challenge["type"], "challenge");
        let server_nonce = challenge["server_nonce"].as_str().unwrap().to_owned();
        (socket, server_nonce)
    }

    pub async fn authenticate(&self) -> (Socket, Value) {
        let (mut socket, server_nonce) = self.connect().await;
        socket
            .send(Message::Text(
                authentication("a", &server_nonce).to_string().into(),
            ))
            .await
            .unwrap();
        let welcome = receive(&mut socket).await;
        assert_eq!(welcome["type"], "welcome");
        (socket, welcome)
    }

    pub async fn finish(self) {
        self.connector.shutdown().await;
        self.server.abort();
        let _ = self.server.await;
        self.database.close().await;
    }
}

pub fn authentication(character: &str, server_nonce: &str) -> Value {
    let token = character.repeat(64);
    let mut message = json!({"type":"authenticate", "protocol_version":1,
        "backend_kind":"thunderbird", "backend_version":"140.4.0",
        "connector_version":"0.1.0", "capabilities":[],
        "client_nonce":"c".repeat(64), "client_proof":"0".repeat(64)});
    let fields: Authenticate = serde_json::from_value(message.clone()).unwrap();
    let transcript = authentication_message(server_nonce, &fields);
    message["client_proof"] = json!(to_hex(&client_proof(&token, &transcript)));
    message
}

pub async fn receive(socket: &mut Socket) -> Value {
    receive_within(socket, Duration::from_secs(2)).await
}

pub async fn receive_within(socket: &mut Socket, limit: Duration) -> Value {
    let frame = tokio::time::timeout(limit, socket.next())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    serde_json::from_str(frame.to_text().unwrap()).unwrap()
}

#[allow(
    dead_code,
    reason = "Each test binary compiles support, and only timing tests use it"
)]
pub async fn elapse(milliseconds: usize) {
    tokio::time::pause();
    tokio::time::advance(Duration::from_millis(milliseconds as u64)).await;
    tokio::time::resume();
}
