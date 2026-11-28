use std::pin::Pin;
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Waker};

use futures_util::{Sink, Stream};
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::{Error, Message};

#[derive(Default)]
pub(super) struct Gate {
    stalled: bool,
    waiting: Option<Waker>,
}

// A socket whose writes block while its gate is stalled and whose reads come from the test.
pub(super) struct StalledSocket {
    pub incoming: mpsc::UnboundedReceiver<Result<Message, Error>>,
    pub written: mpsc::UnboundedSender<String>,
    pub gate: Arc<Mutex<Gate>>,
}

impl Stream for StalledSocket {
    type Item = Result<Message, Error>;

    fn poll_next(mut self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        self.incoming.poll_recv(context)
    }
}

impl Sink<Message> for StalledSocket {
    type Error = Error;

    fn poll_ready(self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<Result<(), Error>> {
        let mut gate = self.gate.lock().unwrap();
        if gate.stalled {
            gate.waiting = Some(context.waker().clone());
            return Poll::Pending;
        }
        Poll::Ready(Ok(()))
    }

    fn start_send(self: Pin<&mut Self>, message: Message) -> Result<(), Error> {
        if let Message::Text(text) = message {
            let _ = self.written.send(text.to_string());
        }
        Ok(())
    }

    fn poll_flush(self: Pin<&mut Self>, _context: &mut Context<'_>) -> Poll<Result<(), Error>> {
        Poll::Ready(Ok(()))
    }

    fn poll_close(self: Pin<&mut Self>, _context: &mut Context<'_>) -> Poll<Result<(), Error>> {
        Poll::Ready(Ok(()))
    }
}

pub(super) fn set_stalled(gate: &Mutex<Gate>, stalled: bool) {
    let mut gate = gate.lock().unwrap();
    gate.stalled = stalled;
    if let (false, Some(waker)) = (stalled, gate.waiting.take()) {
        waker.wake();
    }
}

pub(super) async fn settle() {
    for _ in 0..16 {
        tokio::task::yield_now().await;
    }
}
