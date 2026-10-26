use std::sync::Arc;
use std::time::Duration;

use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::OwnedSemaphorePermit;
use tokio::time::Instant;
use tokio_tungstenite::accept_hdr_async_with_config;

use super::handshake::{self, HandshakeLimit, UpgradeCheck};
use super::{Connector, session};

const ACCEPT_RETRY_DELAY: Duration = Duration::from_millis(100);

impl Connector {
    pub async fn serve(self: Arc<Self>, listener: TcpListener) {
        let mut shutdown = self.shutdown.subscribe();
        loop {
            let accepted = tokio::select! {
                biased;
                _ = shutdown.wait_for(|stopping| *stopping) => return,
                accepted = accept(&self, &listener) => accepted,
            };
            if let Some((stream, socket)) = accepted {
                tokio::spawn(connection(stream, Arc::clone(&self), socket));
            }
        }
    }
}

async fn accept(connector: &Connector, listener: &TcpListener) -> Option<(TcpStream, OwnedSemaphorePermit)> {
    let socket = Arc::clone(&connector.sockets)
        .acquire_owned()
        .await
        .expect("Socket semaphore remains open");
    match listener.accept().await {
        Ok((stream, _)) => Some((stream, socket)),
        Err(_) => {
            tokio::time::sleep(ACCEPT_RETRY_DELAY).await;
            None
        }
    }
}

async fn connection(stream: TcpStream, connector: Arc<Connector>, _socket: OwnedSemaphorePermit) {
    let deadline = Instant::now() + Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64);
    let mut shutdown = connector.shutdown.subscribe();
    let mut pending = None;
    let accepted = {
        let upgrade = accept_hdr_async_with_config(
            HandshakeLimit::new(stream),
            UpgradeCheck {
                connector: &connector,
                pending: &mut pending,
            },
            Some(handshake::config()),
        );
        tokio::select! {
            biased;
            _ = shutdown.wait_for(|stopping| *stopping) => None,
            accepted = tokio::time::timeout_at(deadline, upgrade) => {
                accepted.ok().and_then(Result::ok)
            }
        }
    };
    let (Some(mut socket), Some(pending)) = (accepted, pending) else {
        return;
    };
    socket.get_mut().release();
    session::run(socket, connector, pending, deadline).await;
}
