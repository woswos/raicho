use std::time::Duration;

use axum::extract::ws::{CloseFrame, Message, WebSocket};
use raicho_protocol::contract_generated::{
    Capabilities, Generation, Ping, PingType, ProtocolError, ProtocolErrorType, Welcome,
    WelcomeType,
};
use raicho_protocol::limits_generated::{
    AUTHENTICATION_DEADLINE_MS, HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS, PROTOCOL_VERSION,
};

use super::failure::Failure;
use super::transport::send;

fn protocol_version<Version: TryFrom<i64, Error: std::fmt::Debug>>() -> Version {
    (PROTOCOL_VERSION as i64)
        .try_into()
        .expect("Shared protocol version")
}

pub(super) async fn welcome(
    socket: &mut WebSocket,
    generation: &Generation,
) -> Result<(), Failure> {
    send(
        socket,
        &Welcome {
            capabilities: Capabilities(Vec::new()),
            generation: generation.clone(),
            heartbeat_interval_ms: (HEARTBEAT_INTERVAL_MS as i64)
                .try_into()
                .expect("Shared heartbeat interval"),
            heartbeat_timeout_ms: (HEARTBEAT_TIMEOUT_MS as i64)
                .try_into()
                .expect("Shared heartbeat timeout"),
            protocol_version: protocol_version(),
            type_: WelcomeType::Welcome,
        },
    )
    .await
}

pub(super) async fn ping(
    socket: &mut WebSocket,
    generation: &Generation,
    sequence: u64,
) -> Result<(), Failure> {
    send(
        socket,
        &Ping {
            generation: generation.clone(),
            protocol_version: protocol_version(),
            sequence: sequence.try_into().expect("Positive heartbeat sequence"),
            type_: PingType::Ping,
        },
    )
    .await
}

pub(super) async fn terminate(
    socket: &mut WebSocket,
    generation: Option<&Generation>,
    failure: Failure,
) {
    let frame = ProtocolError {
        code: failure.code,
        generation: generation.cloned(),
        protocol_version: protocol_version(),
        type_: ProtocolErrorType::Error,
    };
    let _ = tokio::time::timeout(
        Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64),
        async {
            if send(socket, &frame).await.is_ok() {
                let _ = socket
                    .send(Message::Close(Some(CloseFrame {
                        code: failure.close_code(),
                        reason: failure.code.to_string().into(),
                    })))
                    .await;
            }
        },
    )
    .await;
}
