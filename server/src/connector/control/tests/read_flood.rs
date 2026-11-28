use std::convert::Infallible;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::task::{Context, Poll};
use std::time::Duration;

use futures_util::{Stream, sink};
use raicho_protocol::channel::{Channel, Peer};
use raicho_protocol::contract_generated::{Generation, ListAccounts, ListAccountsName, Operation};
use raicho_protocol::limits_generated::HEARTBEAT_INTERVAL_MS;
use serde_json::{Value, json};
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::{Error, Message};

use super::super::run;
use crate::connector::{Connector, outbox};
use crate::persistence::Database;

const LATE_REPLIES: usize = 1000;

// Reads frames from the test and counts how many the session has taken.
struct CountedReader {
    incoming: mpsc::UnboundedReceiver<Message>,
    delivered: Arc<AtomicUsize>,
}

impl Stream for CountedReader {
    type Item = Result<Message, Error>;

    fn poll_next(mut self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        let polled = self.incoming.poll_recv(context);
        if let Poll::Ready(Some(_)) = polled {
            self.delivered.fetch_add(1, Ordering::SeqCst);
        }
        polled.map(|message| message.map(Ok))
    }
}

#[tokio::test]
async fn a_flood_of_late_replies_does_not_hold_back_the_ping() {
    let directory = tempfile::tempdir().unwrap();
    let connector = Connector::new(Arc::new(Database::open(directory.path()).await.unwrap()));
    let generation: Generation = "0123456789abcdef0123456789abcdef".parse().unwrap();
    let (_replaced, mut queue) = connector.register(generation.clone()).unwrap();
    let key = [7; 32];
    let mut peer = Channel::new(key, Peer::Client);
    let delivered = Arc::new(AtomicUsize::new(0));
    let (incoming, incoming_receiver) = mpsc::unbounded_channel();
    let mut reader = CountedReader {
        incoming: incoming_receiver,
        delivered: Arc::clone(&delivered),
    };
    let (written_sender, mut written) = mpsc::unbounded_channel();
    let writer = Box::pin(sink::unfold(
        (written_sender, Arc::clone(&delivered)),
        |(sender, delivered), message: Message| async move {
            if let Message::Text(text) = message {
                let frame: Value = serde_json::from_str(text.as_str()).unwrap();
                let _ = sender.send((
                    frame["type"].as_str().unwrap().to_owned(),
                    delivered.load(Ordering::SeqCst),
                ));
            }
            Ok::<_, Infallible>((sender, delivered))
        },
    ));
    tokio::time::pause();
    let session = tokio::spawn({
        let connector = Arc::clone(&connector);
        let generation = generation.clone();
        async move {
            let mut channel = Channel::new(key, Peer::Server);
            let (outbox, mut outgoing) = outbox::channel(writer);
            run(
                &mut reader,
                &connector,
                &generation,
                &mut channel,
                &mut queue,
                &outbox,
                &mut outgoing,
            )
            .await
        }
    });
    let request = tokio::spawn({
        let connector = Arc::clone(&connector);
        async move {
            let operation = Operation::ListAccounts(ListAccounts {
                name: ListAccountsName::ListAccounts,
            });
            connector.request(None, operation).await
        }
    });
    assert_eq!(written.recv().await.unwrap().0, "request");

    // The first reply completes the request, and every copy after it is a late reply the session ignores.
    for _ in 0..=LATE_REPLIES {
        let reply = json!({"type":"reply","protocol_version":2,"generation":generation.as_str(),
            "request_id":1,"result":{"kind":"accounts","accounts":[]}});
        incoming.send(Message::Text(peer.seal(&reply).into())).unwrap();
    }
    // Tokio rounds timer deadlines up to the next millisecond, so the ping is due a moment after the interval.
    tokio::time::advance(Duration::from_millis(HEARTBEAT_INTERVAL_MS as u64 + 1000)).await;
    let (kind, delivered_before_ping) = written.recv().await.unwrap();

    assert_eq!(kind, "ping");
    assert!(
        delivered_before_ping < LATE_REPLIES,
        "{delivered_before_ping} replies were read before the ping"
    );
    assert!(request.await.unwrap().is_ok());
    session.abort();
}
