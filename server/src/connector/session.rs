use std::sync::Arc;

use axum::extract::ws::WebSocket;
use raicho_protocol::diagnostics_generated::BackendError;
use tokio::sync::OwnedSemaphorePermit;

use super::{Connector, authentication, failure::Failure, heartbeat, wire};

pub(super) async fn run(
    mut socket: WebSocket,
    connector: Arc<Connector>,
    pending: OwnedSemaphorePermit,
) {
    let mut shutdown = connector.shutdown.subscribe();
    if *shutdown.borrow() {
        return;
    }
    let authenticated = tokio::select! {
        biased;
        _ = shutdown.changed() => return,
        result = authentication::authenticate(&mut socket, &connector) => result,
    };
    let (generation, mut replaced) = match authenticated {
        Ok(session) => session,
        Err(failure) => {
            connector.reject(failure.diagnostic);
            tokio::select! {
                _ = shutdown.changed() => (),
                _ = wire::terminate(&mut socket, None, failure) => (),
            }
            return;
        }
    };
    drop(pending);
    let result = tokio::select! {
        biased;
        _ = shutdown.changed() => None,
        _ = replaced.changed() => Some(Failure::new(BackendError::SessionReplaced)),
        result = async {
            match wire::welcome(&mut socket, &generation).await {
                Ok(()) => heartbeat::run(&mut socket, &connector, &generation).await,
                Err(error) => error,
            }
        } => Some(result),
    };
    connector.disconnect(
        &generation,
        result.map_or(BackendError::Disconnected, |failure| failure.diagnostic),
    );
    if let Some(failure) = result {
        tokio::select! {
            _ = shutdown.changed() => (),
            _ = wire::terminate(&mut socket, Some(&generation), failure) => (),
        }
    }
}
