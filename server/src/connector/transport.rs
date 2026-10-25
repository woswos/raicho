use axum::extract::ws::{Message, Utf8Bytes, WebSocket};
use raicho_protocol::diagnostics_generated::BackendError;
use tungstenite::error::{Error, ProtocolError};

use super::wire::Failure;

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
