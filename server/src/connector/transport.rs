use std::future::pending;
use std::time::Duration;

use futures_util::{Sink, SinkExt, Stream, StreamExt};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::MAXIMUM_PENDING_REQUESTS;
use serde::Serialize;
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::error::{Error, ProtocolError};
use tokio_tungstenite::tungstenite::{Message, Utf8Bytes};

use super::failure::Failure;

// A peer that stops reading must not hold a session open indefinitely.
pub(super) const WRITE_TIMEOUT: Duration = Duration::from_secs(5);

pub(super) async fn send(socket: &mut (impl Sink<Message> + Unpin), value: &impl Serialize) -> Result<(), Failure> {
    send_text(
        socket,
        serde_json::to_string(value).expect("Connector envelope is serializable"),
    )
    .await
}

pub(super) async fn send_text(socket: &mut (impl Sink<Message> + Unpin), text: String) -> Result<(), Failure> {
    tokio::time::timeout(WRITE_TIMEOUT, socket.send(Message::Text(text.into())))
        .await
        .map_err(|_| Failure::new(BackendError::Disconnected))?
        .map_err(|_| Failure::new(BackendError::Disconnected))
}

// Each pending request leaves at most its request and its cancel queued, beside one ping. Frames
// leave in order, so for a peer that answers only requests it has read, a slot queues a third frame
// only after one of its requests waited unsent past its deadline. A push that finds the queue full
// therefore means a frame waited longer than a request deadline.
const OUTBOX_FRAMES: usize = 2 * MAXIMUM_PENDING_REQUESTS + 1;

/// Sealed frames that the session's one writer sends in order while reads continue.
pub(super) struct Outbox(mpsc::Sender<String>);

impl Outbox {
    pub fn push(&self, text: String) -> Result<(), Failure> {
        self.0
            .try_send(text)
            .map_err(|_| Failure::new(BackendError::Disconnected))
    }
}

pub(super) fn outbox() -> (Outbox, mpsc::Receiver<String>) {
    let (sender, receiver) = mpsc::channel(OUTBOX_FRAMES);
    (Outbox(sender), receiver)
}

pub(super) async fn write_all(
    socket: &mut (impl Sink<Message> + Unpin),
    mut frames: mpsc::Receiver<String>,
) -> Failure {
    while let Some(text) = frames.recv().await {
        if let Err(failure) = send_text(socket, text).await {
            return failure;
        }
    }
    pending().await
}

pub(super) async fn receive_text(
    socket: &mut (impl Stream<Item = Result<Message, Error>> + Unpin),
) -> Result<Utf8Bytes, Failure> {
    loop {
        match socket.next().await {
            Some(Ok(Message::Text(text))) => return Ok(text),
            Some(Ok(Message::Ping(_) | Message::Pong(_))) => {
                // Buffered frames skip Tokio's task budget, so a ping flood must not hold the worker.
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

    use futures_util::sink;
    use raicho_protocol::diagnostics_generated::BackendError;
    use tokio::time::Instant;

    use super::WRITE_TIMEOUT;

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
        assert_eq!(started.elapsed(), WRITE_TIMEOUT);
    }
}
