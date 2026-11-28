use std::sync::Arc;

use futures_util::StreamExt;
use raicho_protocol::diagnostics_generated::BackendError;
use tokio::sync::OwnedSemaphorePermit;
use tokio::time::Instant;

use super::handshake::Socket;
use super::{Connector, authentication, control, failure::Failure, outbox, wire};

pub(super) async fn run(
    mut socket: Socket,
    connector: Arc<Connector>,
    pending: OwnedSemaphorePermit,
    deadline: Instant,
) {
    let mut shutdown = connector.shutdown.subscribe();
    if *shutdown.borrow() {
        return;
    }
    let authenticated = tokio::select! {
        biased;
        _ = shutdown.changed() => return,
        result = authentication::authenticate(&mut socket, &connector, deadline) => result,
    };
    let authentication::Authenticated {
        generation,
        mut replaced,
        server_signature,
        mut channel,
        mut queue,
    } = match authenticated {
        Ok(session) => session,
        Err(failure) => {
            connector.reject(failure.diagnostic);
            tokio::select! {
                _ = shutdown.changed() => (),
                _ = wire::terminate(&mut socket, None, Vec::new(), failure) => (),
            }
            return;
        }
    };
    drop(pending);
    // The write half outlives the control loop, so frames it already accepted reach the peer
    // before the error frame.
    let (writer, mut reader) = socket.split();
    let (outbox, mut outgoing) = outbox::channel(writer);
    let result = tokio::select! {
        biased;
        _ = shutdown.changed() => None,
        _ = replaced.changed() => Some(Failure::new(BackendError::SessionReplaced)),
        result = async {
            match wire::welcome(outgoing.writer(), &generation, &server_signature).await {
                Ok(()) => {
                    control::run(&mut reader, &connector, &generation, &mut channel, &mut queue, &outbox, &mut outgoing)
                        .await
                }
                Err(error) => error,
            }
        } => Some(result),
    };
    connector.disconnect(
        &generation,
        result.map_or(BackendError::Disconnected, |failure| failure.diagnostic),
    );
    if let Some(failure) = result {
        let (mut writer, queued) = outgoing.finish();
        tokio::select! {
            _ = shutdown.changed() => (),
            _ = wire::terminate(&mut writer, Some((&generation, &mut channel)), queued, failure) => (),
        }
    }
}
