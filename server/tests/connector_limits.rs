mod support;

use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS};
use serde_json::json;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::{Message, client::IntoClientRequest};

use support::{Fixture, ORIGIN, receive};

#[tokio::test]
async fn silent_authentication_expires_and_pending_connections_are_bounded() {
    let fixture = Fixture::new().await;
    let mut pending = Vec::new();
    for _ in 0..4 {
        pending.push(fixture.connect().await);
    }
    let mut request = fixture.address.clone().into_client_request().unwrap();
    request
        .headers_mut()
        .insert("Origin", ORIGIN.parse().unwrap());
    assert!(connect_async(request).await.is_err());
    let frame = tokio::time::timeout(Duration::from_secs(6), pending[0].next())
        .await
        .unwrap();
    let message = frame.unwrap().unwrap();
    let error: serde_json::Value = serde_json::from_str(message.to_text().unwrap()).unwrap();
    assert_eq!(error["code"], "authentication_failed");
    let (_replacement, _) = fixture.authenticate().await;
    fixture.finish().await;
}

#[tokio::test]
async fn unsolicited_and_stale_pongs_cannot_satisfy_heartbeat() {
    let fixture = Fixture::new().await;
    for generation in [None, Some("0".repeat(32))] {
        let (mut socket, welcome) = fixture.authenticate().await;
        let expected = if generation.is_some() {
            "stale_generation"
        } else {
            "unexpected_message"
        };
        socket.send(Message::Text(json!({"type":"pong","protocol_version":1,
            "generation": generation.unwrap_or_else(|| welcome["generation"].as_str().unwrap().into()),
            "sequence":1}).to_string().into())).await.unwrap();
        assert_eq!(receive(&mut socket).await["code"], expected);
    }
    fixture.finish().await;
}

#[tokio::test]
async fn heartbeat_accepts_only_its_sequence_and_silent_peers_expire() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome) = fixture.authenticate().await;
    elapse(HEARTBEAT_INTERVAL_MS).await;
    let ping = receive(&mut socket).await;
    socket
        .send(Message::Text(
            json!({"type":"pong","protocol_version":1,
        "generation":welcome["generation"],"sequence":ping["sequence"]})
            .to_string()
            .into(),
        ))
        .await
        .unwrap();
    tokio::time::sleep(Duration::from_millis(20)).await;
    assert_eq!(fixture.connector.snapshot().await.heartbeat_count, 1);
    elapse(HEARTBEAT_INTERVAL_MS).await;
    let next = receive(&mut socket).await;
    assert_eq!(next["sequence"], 2);
    elapse(HEARTBEAT_TIMEOUT_MS).await;
    let timeout = receive(&mut socket).await;
    assert_eq!(timeout["code"], "heartbeat_timeout");
    fixture.finish().await;
}

async fn elapse(milliseconds: usize) {
    tokio::time::pause();
    tokio::time::advance(Duration::from_millis(milliseconds as u64)).await;
    tokio::time::resume();
}

#[tokio::test]
async fn shutdown_cancels_idle_sessions_and_releases_database_users() {
    let fixture = Fixture::new().await;
    let (_active, _) = fixture.authenticate().await;
    let _pending = fixture.connect().await;
    tokio::time::timeout(Duration::from_secs(2), fixture.connector.shutdown())
        .await
        .unwrap();
    assert_eq!(fixture.connector.snapshot().await.status, "disconnected");
    fixture.finish().await;
}
