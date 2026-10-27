use std::time::Duration;

use futures_util::{Sink, SinkExt, StreamExt};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use serde::Serialize;
use tokio_tungstenite::tungstenite::error::{Error, ProtocolError};
use tokio_tungstenite::tungstenite::{Message, Utf8Bytes};

use super::failure::Failure;
use super::handshake::Socket;

pub(super) async fn send(socket: &mut (impl Sink<Message> + Unpin), value: &impl Serialize) -> Result<(), Failure> {
    send_text(
        socket,
        serde_json::to_string(value).expect("Connector envelope is serializable"),
    )
    .await
}

pub(super) async fn send_text(socket: &mut (impl Sink<Message> + Unpin), text: String) -> Result<(), Failure> {
    tokio::time::timeout(
        Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64),
        socket.send(Message::Text(text.into())),
    )
    .await
    .map_err(|_| Failure::new(BackendError::Disconnected))?
    .map_err(|_| Failure::new(BackendError::Disconnected))
}

pub(super) async fn receive_text(socket: &mut Socket) -> Result<Utf8Bytes, Failure> {
    loop {
        match socket.next().await {
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

fn diagnostic(error: Error) -> BackendError {
    match error {
        Error::Io(_)
        | Error::ConnectionClosed
        | Error::AlreadyClosed
        | Error::Protocol(ProtocolError::ResetWithoutClosingHandshake) => BackendError::Disconnected,
        Error::Capacity(_) => BackendError::MessageTooLarge,
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
