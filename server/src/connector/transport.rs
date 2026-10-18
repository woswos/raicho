use axum::extract::ws::{Message, Utf8Bytes, WebSocket};

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
            Some(Err(_)) => return Err(Failure::new("invalid_message")),
        }
    }
}
