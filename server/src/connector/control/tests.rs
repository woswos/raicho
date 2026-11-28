use std::sync::{Arc, Mutex};
use std::time::Duration;

use futures_util::StreamExt;
use raicho_protocol::Phase;
use raicho_protocol::channel::{Channel, Peer};
use raicho_protocol::contract_generated::{ConnectorMessage, Generation, ListAccounts, ListAccountsName, Operation};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::HEARTBEAT_INTERVAL_MS;
use serde_json::json;
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::Message;

mod read_flood;
mod stalled_socket;

use stalled_socket::{Gate, StalledSocket, set_stalled, settle};

use super::run;
use crate::connector::failure::Failure;
use crate::connector::{Connector, outbox, wire};
use crate::persistence::Database;

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
    let socket = StalledSocket {
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
            let (writer, mut reader) = socket.split();
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

#[tokio::test]
async fn a_replaced_session_sends_its_queued_frames_before_the_terminal_frame() {
    let directory = tempfile::tempdir().unwrap();
    let connector = Connector::new(Arc::new(Database::open(directory.path()).await.unwrap()));
    let generation: Generation = "0123456789abcdef0123456789abcdef".parse().unwrap();
    let (_replaced, mut queue) = connector.register(generation.clone()).unwrap();
    let key = [7; 32];
    let mut peer = Channel::new(key, Peer::Client);
    let (_incoming, incoming_receiver) = mpsc::unbounded_channel();
    let (written_sender, mut written) = mpsc::unbounded_channel();
    let gate = Arc::new(Mutex::new(Gate::default()));
    let socket = StalledSocket {
        incoming: incoming_receiver,
        written: written_sender,
        gate: Arc::clone(&gate),
    };
    let (replace, replaced) = tokio::sync::oneshot::channel::<()>();
    tokio::time::pause();
    set_stalled(&gate, true);
    let session = tokio::spawn({
        let connector = Arc::clone(&connector);
        let generation = generation.clone();
        async move {
            let mut channel = Channel::new(key, Peer::Server);
            let (writer, mut reader) = socket.split();
            let (outbox, mut outgoing) = outbox::channel(writer);
            tokio::select! {
                biased;
                _ = replaced => (),
                failure = run(&mut reader, &connector, &generation, &mut channel, &mut queue, &outbox, &mut outgoing) => {
                    panic!("the session ended before its replacement: {:?}", failure.diagnostic);
                }
            }
            let failure = Failure::new(BackendError::SessionReplaced);
            let (mut writer, queued) = outgoing.finish();
            wire::terminate(&mut writer, Some((&generation, &mut channel)), queued, failure).await;
        }
    });

    // The ping waits on the stalled socket, and a request is sealed behind it.
    tokio::time::sleep(Duration::from_millis(HEARTBEAT_INTERVAL_MS as u64)).await;
    settle().await;
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
    replace.send(()).unwrap();
    settle().await;
    set_stalled(&gate, false);
    session.await.unwrap();

    let mut opened = Vec::new();
    while let Ok(frame) = written.try_recv() {
        opened.push(
            peer.open(&frame, Phase::ServerControl, &generation)
                .map(|message| match message {
                    ConnectorMessage::Ping(_) => "ping",
                    ConnectorMessage::Request(_) => "request",
                    ConnectorMessage::ProtocolError(_) => "error",
                    _ => "other",
                }),
        );
    }
    assert_eq!(opened, [Ok("ping"), Ok("request"), Ok("error")]);
    request.abort();
}
