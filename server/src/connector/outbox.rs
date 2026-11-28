use std::future::{pending, poll_fn};

use futures_util::{Sink, SinkExt};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::MAXIMUM_PENDING_REQUESTS;
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::Message;

use super::failure::Failure;
use super::transport::WRITE_TIMEOUT;

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

/// The writer's end of the outbox, which owns the socket's write half. A frame leaves the queue only
/// when the writer accepts it at once, so a cancelled writer leaves every sealed frame either here or
/// inside the writer, ready to be flushed before the session's error frame.
pub(super) struct Outgoing<Writer> {
    writer: Writer,
    frames: mpsc::Receiver<String>,
    held: Option<String>,
}

impl<Writer: Sink<Message> + Unpin> Outgoing<Writer> {
    pub fn writer(&mut self) -> &mut Writer {
        &mut self.writer
    }

    pub async fn write_all(&mut self) -> Failure {
        loop {
            if self.held.is_none() {
                self.held = self.frames.recv().await;
            }
            if self.held.is_none() {
                return pending().await;
            }
            if let Err(failure) = write_held(&mut self.writer, &mut self.held).await {
                return failure;
            }
        }
    }

    /// Returns the writer and the frames sealed but not yet given to it, in the order of their counters.
    pub fn finish(mut self) -> (Writer, Vec<String>) {
        let mut remaining: Vec<String> = self.held.take().into_iter().collect();
        while let Ok(text) = self.frames.try_recv() {
            remaining.push(text);
        }
        (self.writer, remaining)
    }
}

pub(super) fn channel<Writer>(writer: Writer) -> (Outbox, Outgoing<Writer>) {
    let (sender, frames) = mpsc::channel(OUTBOX_FRAMES);
    (
        Outbox(sender),
        Outgoing {
            writer,
            frames,
            held: None,
        },
    )
}

async fn write_held(socket: &mut (impl Sink<Message> + Unpin), held: &mut Option<String>) -> Result<(), Failure> {
    tokio::time::timeout(WRITE_TIMEOUT, async {
        poll_fn(|context| socket.poll_ready_unpin(context))
            .await
            .map_err(disconnected)?;
        let text = held.take().expect("The writer holds a frame");
        socket
            .start_send_unpin(Message::Text(text.into()))
            .map_err(disconnected)?;
        socket.flush().await.map_err(disconnected)
    })
    .await
    .map_err(disconnected)?
}

fn disconnected<Cause>(_: Cause) -> Failure {
    Failure::new(BackendError::Disconnected)
}
