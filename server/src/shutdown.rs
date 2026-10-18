use std::future::IntoFuture;
use std::pin::pin;
use std::sync::Arc;
use std::time::Duration;

use axum::Router;
use tokio::net::TcpListener;
use tokio::signal::unix::{SignalKind, signal};
use tokio::sync::watch;

use raicho_server::connector::{Connector, ConnectorListener};
use raicho_server::error::{Error, Result};

pub async fn serve(
    listener: TcpListener,
    application: Router,
    connector_listener: TcpListener,
    connector: Arc<Connector>,
) -> Result<()> {
    let mut terminate = signal(SignalKind::terminate())
        .map_err(|error| Error::new("Cannot register SIGTERM handler", error))?;
    let mut interrupt = signal(SignalKind::interrupt())
        .map_err(|error| Error::new("Cannot register SIGINT handler", error))?;
    let (sender, receiver) = watch::channel(false);
    let public = axum::serve(listener, application)
        .with_graceful_shutdown(stop(receiver.clone()))
        .into_future();
    let internal = axum::serve(
        ConnectorListener::new(connector_listener),
        connector.router(),
    )
    .with_graceful_shutdown(stop(receiver))
    .into_future();
    let servers = async { tokio::try_join!(public, internal).map(|_| ()) };
    let mut servers = pin!(servers);
    let completed = tokio::select! {
        result = &mut servers => Some(result),
        _ = terminate.recv() => None,
        _ = interrupt.recv() => None,
    };
    sender.send_replace(true);
    connector.shutdown().await;
    match completed {
        Some(result) => result.map_err(|error| Error::new("Application listener failed", error)),
        None => tokio::time::timeout(Duration::from_secs(10), servers)
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
