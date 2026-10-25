use axum::extract::ws::{Message, Utf8Bytes, WebSocket};
use tungstenite::error::{Error, ProtocolError};

use super::wire::Failure;

pub(super) async fn receive_text(socket: &mut WebSocket) -> Result<Utf8Bytes, Failure> {
    loop {
        match socket.recv().await {
            Some(Ok(Message::Text(text))) => return Ok(text),
            Some(Ok(Message::Ping(_) | Message::Pong(_))) => {
                tokio::task::yield_now().await;
            }
            Some(Ok(Message::Close(_))) | None => return Err(Failure::new("disconnected")),
            Some(Ok(_)) => return Err(Failure::new("unexpected_message")),
            Some(Err(error)) => return Err(Failure::new(diagnostic(error))),
        }
    }
}

fn diagnostic(error: axum::Error) -> &'static str {
    match error.into_inner().downcast::<Error>().map(|error| *error) {
        Ok(
            Error::Io(_)
            | Error::ConnectionClosed
            | Error::AlreadyClosed
            | Error::Protocol(ProtocolError::ResetWithoutClosingHandshake),
        ) => "disconnected",
        Ok(Error::Capacity(_)) => "message_too_large",
        _ => "invalid_message",
    }
}
