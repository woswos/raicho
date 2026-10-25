mod support;

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::tungstenite::protocol::frame::{
    Frame,
    coding::{Data, OpCode},
};

use support::{Fixture, receive, receive_within};

#[tokio::test]
async fn fragmented_authentication_cannot_extend_the_absolute_deadline() {
    let fixture = Fixture::new().await;
    let (mut socket, _) = fixture.connect().await;
    socket
        .send(Message::Frame(Frame::message(
            vec![b'{'],
            OpCode::Data(Data::Text),
            false,
        )))
        .await
        .unwrap();
    tokio::time::sleep(Duration::from_secs(3)).await;
    socket
        .send(Message::Frame(Frame::message(
            vec![b' '],
            OpCode::Data(Data::Continue),
            false,
        )))
        .await
        .unwrap();
    let error = receive_within(&mut socket, Duration::from_secs(3)).await;
    assert_eq!(error["code"], "authentication_failed");
    assert_eq!(
        fixture.connector.snapshot().await.last_error,
        Some(BackendError::AuthenticationTimeout)
    );
    fixture.finish().await;
}

#[tokio::test]
async fn binary_frames_are_terminal_before_authentication() {
    let fixture = Fixture::new().await;
    let (mut socket, _) = fixture.connect().await;
    socket.send(Message::Binary(vec![1].into())).await.unwrap();
    assert_eq!(receive(&mut socket).await["code"], "unexpected_message");
    fixture.finish().await;
}

#[tokio::test]
async fn fragmented_messages_obey_the_transport_aggregate_budget() {
    let fixture = Fixture::new().await;
    let (mut socket, _) = fixture.authenticate().await;
    socket
        .send(Message::Frame(Frame::message(
            vec![b' '; 40000],
            OpCode::Data(Data::Text),
            false,
        )))
        .await
        .unwrap();
    let _ = socket
        .send(Message::Frame(Frame::message(
            vec![b' '; 40000],
            OpCode::Data(Data::Continue),
            true,
        )))
        .await;
    let _ = tokio::time::timeout(Duration::from_secs(2), socket.next())
        .await
        .unwrap();
    tokio::time::sleep(Duration::from_millis(20)).await;
    let status = fixture.connector.snapshot().await;
    assert_eq!(status.status, BackendState::Disconnected);
    assert_eq!(status.last_error, Some(BackendError::MessageTooLarge));
    fixture.finish().await;
}

#[tokio::test]
async fn abrupt_peer_loss_is_recorded_as_a_disconnection() {
    let fixture = Fixture::new().await;
    let (socket, _) = fixture.authenticate().await;
    drop(socket);
    tokio::time::sleep(Duration::from_millis(20)).await;
    let status = fixture.connector.snapshot().await;
    assert_eq!(status.status, BackendState::Disconnected);
    assert_eq!(status.last_error, Some(BackendError::Disconnected));
    fixture.finish().await;
}
