mod support;

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use std::time::Duration;

use futures_util::SinkExt;
use raicho_protocol::Phase;
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS};
use serde_json::json;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::Message;

use support::{Fixture, elapse, receive, receive_within};

#[tokio::test]
async fn silent_authentication_expires_and_pending_connections_are_bounded() {
    let fixture = Fixture::new().await;
    let mut pending = Vec::new();
    for _ in 0..4 {
        pending.push(fixture.connect().await.0);
    }
    assert!(connect_async(fixture.request()).await.is_err());
    let error = receive_within(&mut pending[0], Duration::from_secs(6)).await;
    assert_eq!(error["code"], "authentication_failed");
    let (_replacement, _) = fixture.authenticate().await;
    fixture.finish().await;
}

#[tokio::test]
async fn unsolicited_and_stale_pongs_cannot_satisfy_heartbeat() {
    let fixture = Fixture::new().await;
    for generation in [None, Some("0".repeat(32))] {
        let (mut socket, welcome, mut channel) = fixture.session().await;
        let expected = if generation.is_some() {
            "stale_generation"
        } else {
            "unexpected_message"
        };
        let pong = json!({"type":"pong","protocol_version":1,
            "generation": generation.unwrap_or_else(|| welcome["generation"].as_str().unwrap().into()),
            "sequence":1});
        socket.send(Message::Text(channel.seal(&pong).into())).await.unwrap();
        assert_eq!(receive(&mut socket).await["code"], expected);
    }
    fixture.finish().await;
}

#[tokio::test]
async fn heartbeat_accepts_only_its_sequence_and_silent_peers_expire() {
    let fixture = Fixture::new().await;
    let (mut socket, welcome, mut channel) = fixture.session().await;
    let generation = welcome["generation"].as_str().unwrap();
    elapse(HEARTBEAT_INTERVAL_MS).await;
    let ping = receive(&mut socket).await;
    channel
        .open(&ping.to_string(), Phase::ServerControl, generation)
        .unwrap();
    let pong = json!({"type":"pong","protocol_version":1,
        "generation":generation,"sequence":ping["sequence"]});
    socket.send(Message::Text(channel.seal(&pong).into())).await.unwrap();
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

#[tokio::test]
async fn forged_and_replayed_pongs_end_the_session_with_a_sealed_error() {
    let fixture = Fixture::new().await;
    for replay in [false, true] {
        let (mut socket, welcome, mut channel) = fixture.session().await;
        let generation = welcome["generation"].as_str().unwrap();
        elapse(HEARTBEAT_INTERVAL_MS).await;
        let ping = receive(&mut socket).await;
        channel
            .open(&ping.to_string(), Phase::ServerControl, generation)
            .unwrap();
        let pong = channel.seal(&json!({"type":"pong","protocol_version":1,
            "generation":generation,"sequence":ping["sequence"]}));
        let rejected = if replay {
            socket.send(Message::Text(pong.clone().into())).await.unwrap();
            tokio::time::sleep(Duration::from_millis(20)).await;
            elapse(HEARTBEAT_INTERVAL_MS).await;
            let next = receive(&mut socket).await;
            channel
                .open(&next.to_string(), Phase::ServerControl, generation)
                .unwrap();
            pong
        } else {
            pong.replace("\"sequence\":1", "\"sequence\":2")
        };
        socket.send(Message::Text(rejected.into())).await.unwrap();
        let error = receive(&mut socket).await;
        assert_eq!(error["code"], "authentication_failed");
        channel
            .open(&error.to_string(), Phase::ServerControl, generation)
            .unwrap();
        assert_eq!(
            fixture.connector.snapshot().await.last_error,
            Some(BackendError::AuthenticationFailed)
        );
    }
    fixture.finish().await;
}

#[tokio::test]
async fn shutdown_cancels_idle_sessions_and_releases_database_users() {
    let fixture = Fixture::new().await;
    let (_active, _) = fixture.authenticate().await;
    let _pending = fixture.connect().await;
    tokio::time::timeout(Duration::from_secs(2), fixture.connector.shutdown())
        .await
        .unwrap();
    assert_eq!(fixture.connector.snapshot().await.status, BackendState::Disconnected);
    fixture.finish().await;
}
