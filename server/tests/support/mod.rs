use std::sync::Arc;
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use raicho_server::connector::{Connector, ConnectorListener};
use raicho_server::credentials::{Credential, CredentialStore};
use raicho_server::persistence::Database;
use serde_json::{Value, json};
use tempfile::TempDir;
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::tungstenite::{Message, client::IntoClientRequest};
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

    pub async fn connect(&self) -> Socket {
        let mut request = self.address.clone().into_client_request().unwrap();
        request
            .headers_mut()
            .insert("Origin", ORIGIN.parse().unwrap());
        connect_async(request).await.unwrap().0
    }

    pub async fn authenticate(&self) -> (Socket, Value) {
        let mut socket = self.connect().await;
        socket
            .send(Message::Text(authentication("a").to_string().into()))
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

pub fn authentication(character: &str) -> Value {
    json!({"type":"authenticate", "protocol_version":1, "token":character.repeat(64),
        "backend_kind":"thunderbird", "backend_version":"140.4.0",
        "connector_version":"0.1.0", "capabilities":[]})
}

pub async fn receive(socket: &mut Socket) -> Value {
    let frame = tokio::time::timeout(Duration::from_secs(2), socket.next())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    serde_json::from_str(frame.to_text().unwrap()).unwrap()
}
