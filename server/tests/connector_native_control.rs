mod support;

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS};
use tokio_tungstenite::tungstenite::Message;

use support::{Fixture, Socket, authentication, elapse, receive};

#[tokio::test]
async fn native_ping_and_pong_are_transport_controls_before_and_after_authentication() {
    let fixture = Fixture::new().await;
    let mut socket = fixture.connect().await;
    socket.send(Message::Pong(vec![1].into())).await.unwrap();
    native_ping(&mut socket).await;
    socket
        .send(Message::Text(authentication("a").to_string().into()))
        .await
        .unwrap();
    assert_eq!(receive(&mut socket).await["type"], "welcome");
    native_ping(&mut socket).await;
    socket.send(Message::Pong(vec![2].into())).await.unwrap();
    assert_eq!(
        fixture.connector.snapshot().await.status,
        BackendState::Connected
    );
    assert_eq!(fixture.connector.snapshot().await.heartbeat_count, 0);
    fixture.finish().await;
}

#[tokio::test]
async fn native_controls_do_not_restart_the_authentication_deadline() {
    let fixture = Fixture::new().await;
    let mut socket = fixture.connect().await;
    for _ in 0..2 {
        elapse(2000).await;
        native_ping(&mut socket).await;
    }
    elapse(1001).await;
    assert_eq!(receive(&mut socket).await["code"], "authentication_failed");
    assert_eq!(
        fixture.connector.snapshot().await.last_error,
        Some(BackendError::AuthenticationTimeout)
    );
    fixture.finish().await;
}

#[tokio::test]
async fn native_control_flood_never_satisfies_or_delays_the_application_heartbeat() {
    let fixture = Fixture::new().await;
    let (mut socket, _) = fixture.authenticate().await;
    elapse(HEARTBEAT_INTERVAL_MS).await;
    assert_eq!(receive(&mut socket).await["type"], "ping");
    for _ in 0..8 {
        for _ in 0..32 {
            socket.send(Message::Pong(vec![1].into())).await.unwrap();
        }
        native_ping(&mut socket).await;
        elapse(5000).await;
    }
    assert_eq!(fixture.connector.snapshot().await.heartbeat_count, 0);
    elapse(HEARTBEAT_TIMEOUT_MS - 40000 + 1).await;
    assert_eq!(receive(&mut socket).await["code"], "heartbeat_timeout");
    fixture.finish().await;
}

async fn native_ping(socket: &mut Socket) {
    socket
        .send(Message::Ping(vec![7, 8, 9].into()))
        .await
        .unwrap();
    let frame = tokio::time::timeout(Duration::from_secs(2), socket.next())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    assert!(matches!(frame, Message::Pong(contents) if contents.as_ref() == [7, 8, 9]));
}
