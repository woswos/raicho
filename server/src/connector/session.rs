use std::sync::Arc;
use std::time::Duration;

use axum::extract::ws::WebSocket;
use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use tokio::sync::OwnedSemaphorePermit;

use super::{
    Connector, authentication, heartbeat,
    wire::{self, Failure},
};

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
        result = tokio::time::timeout(
            Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64),
            authentication::authenticate(&mut socket, &connector),
        ) => result.unwrap_or_else(|_| Err(Failure::new("authentication_timeout"))),
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
        _ = replaced.changed() => Some(Failure::new("session_replaced")),
        result = async {
            match wire::welcome(&mut socket, &generation).await {
                Ok(()) => heartbeat::run(&mut socket, &connector, &generation).await,
                Err(error) => error,
            }
        } => Some(result),
    };
    connector.disconnect(
        &generation,
        result.map_or("disconnected", |failure| failure.diagnostic),
    );
    if let Some(failure) = result {
        tokio::select! {
            _ = shutdown.changed() => (),
            _ = wire::terminate(&mut socket, Some(&generation), failure) => (),
        }
    }
}
