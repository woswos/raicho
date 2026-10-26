use std::future::IntoFuture;
use std::pin::pin;
use std::sync::Arc;
use std::time::Duration;

use axum::Router;
use tokio::net::TcpListener;
use tokio::signal::unix::{SignalKind, signal};
use tokio::sync::watch;

use raicho_server::connector::Connector;
use raicho_server::error::{Error, Result};

pub async fn serve(
    listener: TcpListener,
    application: Router,
    connector_listener: TcpListener,
    connector: Arc<Connector>,
) -> Result<()> {
    let mut terminate =
        signal(SignalKind::terminate()).map_err(|error| Error::new("Cannot register SIGTERM handler", error))?;
    let mut interrupt =
        signal(SignalKind::interrupt()).map_err(|error| Error::new("Cannot register SIGINT handler", error))?;
    let (sender, receiver) = watch::channel(false);
    // The accept loop holds a socket permit until it sees shutdown, so it must keep running.
    let internal = tokio::spawn(Arc::clone(&connector).serve(connector_listener));
    let public = axum::serve(listener, application)
        .with_graceful_shutdown(stop(receiver))
        .into_future();
    let mut public = pin!(public);
    let completed = tokio::select! {
        result = &mut public => Some(result),
        _ = terminate.recv() => None,
        _ = interrupt.recv() => None,
    };
    sender.send_replace(true);
    connector.shutdown().await;
    internal
        .await
        .map_err(|error| Error::new("Connector listener failed", error))?;
    match completed {
        Some(result) => result.map_err(|error| Error::new("Application listener failed", error)),
        None => tokio::time::timeout(Duration::from_secs(10), public)
            .await
            .map_err(|error| Error::new("Application listeners shutdown timed out", error))?
            .map_err(|error| Error::new("Application listener failed during shutdown", error)),
    }
}

async fn stop(mut receiver: watch::Receiver<bool>) {
    if !*receiver.borrow() {
        let _ = receiver.changed().await;
    }
}
