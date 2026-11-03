use std::sync::Arc;
use std::time::Duration;

use futures_util::SinkExt;
use raicho_protocol::Phase;
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{Generation, ListAccounts, ListAccountsName, Operation, Outcome};
use raicho_protocol::diagnostics_generated::BackendState;
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, MAXIMUM_PENDING_REQUESTS, REQUEST_TIMEOUT_MS};
use raicho_server::connector::{Connector, RequestFailure};
use serde_json::{Value, json};
use tokio::task::JoinHandle;
use tokio_tungstenite::tungstenite::Message;

use crate::support::{Fixture, Socket, elapse, receive};

fn list_accounts() -> Operation {
    Operation::ListAccounts(ListAccounts {
        name: ListAccountsName::ListAccounts,
    })
}

fn spawn_request(connector: &Arc<Connector>) -> JoinHandle<Result<(Generation, Outcome), RequestFailure>> {
    let connector = Arc::clone(connector);
    tokio::spawn(async move { connector.request(None, list_accounts()).await })
}

async fn open(socket: &mut Socket, channel: &mut Channel, generation: &str) -> Value {
    let frame = receive(socket).await;
    channel
        .open(&frame.to_string(), Phase::ServerControl, generation)
        .unwrap();
    frame
}

async fn reply(socket: &mut Socket, channel: &mut Channel, generation: &str, request_id: &Value, result: Value) {
    let frame = json!({"type":"reply","protocol_version":2,"generation":generation,
        "request_id":request_id,"result":result});
    socket.send(Message::Text(channel.seal(&frame).into())).await.unwrap();
}

fn accounts() -> Value {
    json!({"kind":"accounts","accounts":[{"id":"A".repeat(22),"name":"Zoë","identities":[]}]})
}

#[tokio::test]
async fn a_request_receives_its_reply_with_the_session_generation() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    let pending = spawn_request(&fixture.connector);
    let request = open(&mut socket, &mut channel, generation).await;
    assert_eq!(request["type"], "request");
    assert_eq!(request["request_id"], 1);
    assert_eq!(request["operation"], json!({"name":"list_accounts"}));
    reply(
        &mut socket,
        &mut channel,
        generation,
        &request["request_id"],
        accounts(),
    )
    .await;
    let (active, outcome) = pending.await.unwrap().unwrap();
    assert_eq!(active.as_str(), generation);
    let Outcome::AccountsResult(result) = outcome else {
        panic!("Expected accounts");
    };
    assert_eq!(result.accounts[0].name.as_str(), "Zoë");
    fixture.finish().await;
}

#[tokio::test]
async fn requests_fail_without_a_session_or_for_another_generation() {
    let fixture = Fixture::new().await;
    assert_eq!(
        fixture.connector.request(None, list_accounts()).await.err(),
        Some(RequestFailure::Disconnected)
    );
    let (_socket, _welcome, _channel) = fixture.session().await;
    let other: Generation = "f".repeat(32).parse().unwrap();
    assert_eq!(
        fixture.connector.request(Some(&other), list_accounts()).await.err(),
        Some(RequestFailure::StaleGeneration)
    );
    fixture.finish().await;
}

#[tokio::test]
async fn an_expired_request_is_cancelled_and_its_late_reply_is_ignored() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    let pending = spawn_request(&fixture.connector);
    let request = open(&mut socket, &mut channel, generation).await;
    // The request deadline and the first heartbeat share one interval, so both frames arrive.
    elapse(REQUEST_TIMEOUT_MS).await;
    let mut frames = vec![
        open(&mut socket, &mut channel, generation).await,
        open(&mut socket, &mut channel, generation).await,
    ];
    frames.sort_by_key(|frame| frame["type"].as_str().unwrap().to_owned());
    let [cancel, ping] = <[Value; 2]>::try_from(frames).unwrap();
    assert_eq!(cancel["type"], "cancel");
    assert_eq!(cancel["request_id"], request["request_id"]);
    assert_eq!(pending.await.unwrap().err(), Some(RequestFailure::Timeout));
    reply(
        &mut socket,
        &mut channel,
        generation,
        &request["request_id"],
        accounts(),
    )
    .await;
    pong(&mut socket, &mut channel, generation, &ping).await;
    tokio::time::timeout(Duration::from_secs(2), async {
        while fixture.connector.snapshot().await.heartbeat_count == 0 {
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await
    .unwrap();
    assert_eq!(fixture.connector.snapshot().await.status, BackendState::Connected);
    fixture.finish().await;
}

async fn pong(socket: &mut Socket, channel: &mut Channel, generation: &str, ping: &Value) {
    assert_eq!(ping["type"], "ping");
    let pong = json!({"type":"pong","protocol_version":2,"generation":generation,"sequence":ping["sequence"]});
    socket.send(Message::Text(channel.seal(&pong).into())).await.unwrap();
}

#[tokio::test]
async fn a_reply_to_a_request_never_sent_ends_the_session() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    reply(&mut socket, &mut channel, generation, &json!(1), accounts()).await;
    let error = open(&mut socket, &mut channel, generation).await;
    assert_eq!(error["code"], "unexpected_message");
    fixture.finish().await;
}

#[tokio::test]
async fn a_disconnect_fails_requests_that_await_a_reply() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    let pending = spawn_request(&fixture.connector);
    open(&mut socket, &mut channel, generation).await;
    drop(socket);
    assert_eq!(pending.await.unwrap().err(), Some(RequestFailure::Disconnected));
    fixture.finish().await;
}

#[tokio::test]
async fn the_queue_and_pending_replies_are_bounded() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    let mut pending: Vec<_> = (0..MAXIMUM_PENDING_REQUESTS)
        .map(|_| spawn_request(&fixture.connector))
        .collect();
    let mut sent = Vec::new();
    for _ in 0..MAXIMUM_PENDING_REQUESTS {
        sent.push(open(&mut socket, &mut channel, generation).await["request_id"].clone());
    }
    pending.extend((0..MAXIMUM_PENDING_REQUESTS).map(|_| spawn_request(&fixture.connector)));
    tokio::time::sleep(Duration::from_millis(50)).await;
    assert_eq!(
        fixture.connector.request(None, list_accounts()).await.err(),
        Some(RequestFailure::Busy)
    );
    for request_id in &sent {
        reply(&mut socket, &mut channel, generation, request_id, accounts()).await;
    }
    for _ in 0..MAXIMUM_PENDING_REQUESTS {
        let request = open(&mut socket, &mut channel, generation).await;
        reply(
            &mut socket,
            &mut channel,
            generation,
            &request["request_id"],
            accounts(),
        )
        .await;
    }
    for request in pending.drain(..) {
        assert!(request.await.unwrap().is_ok());
    }
    fixture.finish().await;
}

#[tokio::test]
async fn heartbeat_continues_while_a_request_awaits_its_reply() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    elapse(HEARTBEAT_INTERVAL_MS).await;
    let ping = open(&mut socket, &mut channel, generation).await;
    let pending = spawn_request(&fixture.connector);
    let request = open(&mut socket, &mut channel, generation).await;
    assert_eq!(request["type"], "request");
    pong(&mut socket, &mut channel, generation, &ping).await;
    reply(
        &mut socket,
        &mut channel,
        generation,
        &request["request_id"],
        accounts(),
    )
    .await;
    assert!(pending.await.unwrap().is_ok());
    assert_eq!(fixture.connector.snapshot().await.heartbeat_count, 1);
    fixture.finish().await;
}
