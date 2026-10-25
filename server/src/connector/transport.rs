use std::time::Duration;

use axum::extract::ws::{Message, Utf8Bytes, WebSocket};
use futures_util::{Sink, SinkExt};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use serde::Serialize;
use tungstenite::error::{Error, ProtocolError};

use super::failure::Failure;

pub(super) async fn send(
    socket: &mut (impl Sink<Message> + Unpin),
    value: &impl Serialize,
) -> Result<(), Failure> {
    let text = serde_json::to_string(value).expect("Connector envelope is serializable");
    tokio::time::timeout(
        Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64),
        socket.send(Message::Text(text.into())),
    )
    .await
    .map_err(|_| Failure::new(BackendError::Disconnected))?
    .map_err(|_| Failure::new(BackendError::Disconnected))
}

pub(super) async fn receive_text(socket: &mut WebSocket) -> Result<Utf8Bytes, Failure> {
    loop {
        match socket.recv().await {
            Some(Ok(Message::Text(text))) => return Ok(text),
            Some(Ok(Message::Ping(_) | Message::Pong(_))) => {
                tokio::task::yield_now().await;
            }
            Some(Ok(Message::Close(_))) | None => {
                return Err(Failure::new(BackendError::Disconnected));
            }
            Some(Ok(_)) => return Err(Failure::new(BackendError::UnexpectedMessage)),
            Some(Err(error)) => return Err(Failure::new(diagnostic(error))),
        }
    }
}

fn diagnostic(error: axum::Error) -> BackendError {
    match error.into_inner().downcast::<Error>().map(|error| *error) {
        Ok(
            Error::Io(_)
            | Error::ConnectionClosed
            | Error::AlreadyClosed
            | Error::Protocol(ProtocolError::ResetWithoutClosingHandshake),
        ) => BackendError::Disconnected,
        Ok(Error::Capacity(_)) => BackendError::MessageTooLarge,
        _ => BackendError::InvalidMessage,
    }
}

#[cfg(test)]
mod tests {
    use std::convert::Infallible;
    use std::future::pending;
    use std::time::Duration;

    use futures_util::sink;
    use raicho_protocol::diagnostics_generated::BackendError;
    use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
    use tokio::time::Instant;

    #[tokio::test(start_paused = true)]
    async fn blocked_peer_flush_expires_without_an_unbounded_outgoing_queue() {
        let mut blocked_peer = Box::pin(sink::unfold((), |(), _frame| async {
            pending::<Result<(), Infallible>>().await
        }));
        let started = Instant::now();
        let failure = super::send(&mut blocked_peer, &serde_json::json!({"type": "ping"}))
            .await
            .err()
            .unwrap();
        assert_eq!(failure.diagnostic, BackendError::Disconnected);
        assert_eq!(
            started.elapsed(),
            Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64)
        );
    }
}
