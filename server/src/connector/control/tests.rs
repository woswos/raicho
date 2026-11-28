use std::pin::Pin;
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Waker};
use std::time::Duration;

use futures_util::{Sink, Stream};
use raicho_protocol::Phase;
use raicho_protocol::channel::{Channel, Peer};
use raicho_protocol::contract_generated::{ConnectorMessage, Generation, ListAccounts, ListAccountsName, Operation};
use raicho_protocol::limits_generated::HEARTBEAT_INTERVAL_MS;
use serde_json::json;
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::{Error, Message};

use super::run;
use crate::connector::Connector;
use crate::persistence::Database;

#[derive(Default)]
struct Gate {
    stalled: bool,
    waiting: Option<Waker>,
}

// A socket whose writes block while its gate is stalled and whose reads come from the test.
struct StalledSocket {
    incoming: mpsc::UnboundedReceiver<Result<Message, Error>>,
    written: mpsc::UnboundedSender<String>,
    gate: Arc<Mutex<Gate>>,
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
        let _ = self.written.send(message.into_text().unwrap().to_string());
        Ok(())
    }

    fn poll_flush(self: Pin<&mut Self>, _context: &mut Context<'_>) -> Poll<Result<(), Error>> {
        Poll::Ready(Ok(()))
    }

    fn poll_close(self: Pin<&mut Self>, _context: &mut Context<'_>) -> Poll<Result<(), Error>> {
        Poll::Ready(Ok(()))
    }
}

fn set_stalled(gate: &Mutex<Gate>, stalled: bool) {
    let mut gate = gate.lock().unwrap();
    gate.stalled = stalled;
    if let (false, Some(waker)) = (stalled, gate.waiting.take()) {
        waker.wake();
    }
}

async fn settle() {
    for _ in 0..16 {
        tokio::task::yield_now().await;
    }
}

#[tokio::test]
async fn a_pong_that_arrives_during_a_stalled_write_keeps_the_session() {
    let directory = tempfile::tempdir().unwrap();
    let connector = Connector::new(Arc::new(Database::open(directory.path()).await.unwrap()));
    let generation: Generation = "0123456789abcdef0123456789abcdef".parse().unwrap();
    let (_replaced, mut queue) = connector.register(generation.clone()).unwrap();
    let key = [7; 32];
    let mut peer = Channel::new(key, Peer::Client);
    let (incoming, incoming_receiver) = mpsc::unbounded_channel();
    let (written_sender, mut written) = mpsc::unbounded_channel();
    let gate = Arc::new(Mutex::new(Gate::default()));
    let mut socket = StalledSocket {
        incoming: incoming_receiver,
        written: written_sender,
        gate: Arc::clone(&gate),
    };
    tokio::time::pause();
    let session = tokio::spawn({
        let connector = Arc::clone(&connector);
        let generation = generation.clone();
        async move {
            let mut channel = Channel::new(key, Peer::Server);
            run(&mut socket, &connector, &generation, &mut channel, &mut queue).await
        }
    });
    tokio::time::sleep(Duration::from_millis(HEARTBEAT_INTERVAL_MS as u64)).await;
    settle().await;
    let ConnectorMessage::Ping(ping) = peer
        .open(&written.recv().await.unwrap(), Phase::ServerControl, &generation)
        .unwrap()
    else {
        panic!("expected a ping");
    };

    // The pong is due 45 seconds after the ping. The request write stalls from 42 to 46 seconds.
    tokio::time::advance(Duration::from_secs(42)).await;
    set_stalled(&gate, true);
    let request = tokio::spawn({
        let connector = Arc::clone(&connector);
        async move {
            let operation = Operation::ListAccounts(ListAccounts {
                name: ListAccountsName::ListAccounts,
            });
            connector.request(None, operation).await
        }
    });
    settle().await;
    tokio::time::advance(Duration::from_secs(1)).await;
    let pong =
        json!({"type":"pong","protocol_version":2,"generation":generation.as_str(),"sequence":ping.sequence.get()});
    incoming.send(Ok(Message::Text(peer.seal(&pong).into()))).unwrap();
    settle().await;
    tokio::time::advance(Duration::from_secs(3)).await;
    set_stalled(&gate, false);
    settle().await;

    assert!(!session.is_finished(), "{:?}", session.await.unwrap().diagnostic);
    assert_eq!(connector.snapshot().await.heartbeat_count, 1);
    let sent = written.recv().await.unwrap();
    assert!(matches!(
        peer.open(&sent, Phase::ServerControl, &generation).unwrap(),
        ConnectorMessage::Request(_)
    ));
    session.abort();
    request.abort();
}
