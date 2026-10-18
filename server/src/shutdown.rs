use std::future::IntoFuture;
use std::pin::pin;
use std::time::Duration;

use axum::Router;
use tokio::net::TcpListener;
use tokio::signal::unix::{SignalKind, signal};
use tokio::sync::oneshot;

use raicho_server::error::{Error, Result};

pub async fn serve(listener: TcpListener, application: Router) -> Result<()> {
    let mut terminate = signal(SignalKind::terminate())
        .map_err(|error| Error::new("Cannot register SIGTERM handler", error))?;
    let mut interrupt = signal(SignalKind::interrupt())
        .map_err(|error| Error::new("Cannot register SIGINT handler", error))?;
    let (sender, receiver) = oneshot::channel();
    let server = axum::serve(listener, application)
        .with_graceful_shutdown(async {
            let _ = receiver.await;
        })
        .into_future();
    let mut server = pin!(server);
    tokio::select! {
        result = &mut server => return result.map_err(|error| Error::new("HTTP server failed", error)),
        _ = terminate.recv() => (),
        _ = interrupt.recv() => (),
    }
    let _ = sender.send(());
    tokio::time::timeout(Duration::from_secs(10), server)
        .await
        .map_err(|error| Error::new("HTTP shutdown timed out", error))?
        .map_err(|error| Error::new("HTTP server failed during shutdown", error))
}
