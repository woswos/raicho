use std::io;
use std::net::SocketAddr;
use std::sync::Arc;

use axum::serve::Listener;
use raicho_protocol::limits_generated::MAXIMUM_PENDING_AUTHENTICATIONS;
use tokio::net::TcpListener;
use tokio::sync::Semaphore;

use super::CONNECTION_LIMIT;
use super::upgrade_stream::UpgradeStream;

pub struct ConnectorListener {
    listener: TcpListener,
    connections: Arc<Semaphore>,
}

impl ConnectorListener {
    pub fn new(listener: TcpListener) -> Self {
        Self {
            listener,
            connections: Arc::new(Semaphore::new(
                CONNECTION_LIMIT + MAXIMUM_PENDING_AUTHENTICATIONS,
            )),
        }
    }
}

impl Listener for ConnectorListener {
    type Io = UpgradeStream;
    type Addr = SocketAddr;

    async fn accept(&mut self) -> (Self::Io, Self::Addr) {
        let permit = Arc::clone(&self.connections)
            .acquire_owned()
            .await
            .expect("Listener semaphore remains open");
        let (stream, address) = Listener::accept(&mut self.listener).await;
        (UpgradeStream::new(stream, permit), address)
    }

    fn local_addr(&self) -> io::Result<Self::Addr> {
        self.listener.local_addr()
    }
}
