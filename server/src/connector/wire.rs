use std::time::Duration;

use axum::extract::ws::{CloseFrame, Message, WebSocket};
use futures_util::{Sink, SinkExt};
use raicho_protocol::ContractError;
use raicho_protocol::contract_generated::{
    Capabilities, Generation, Ping, PingType, ProtocolError, ProtocolErrorCode, ProtocolErrorType,
    Welcome, WelcomeType,
};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{
    AUTHENTICATION_DEADLINE_MS, AUTHENTICATION_FAILURE_CLOSE_CODE, HEARTBEAT_INTERVAL_MS,
    HEARTBEAT_TIMEOUT_MS, PROTOCOL_FAILURE_CLOSE_CODE, PROTOCOL_VERSION,
    SESSION_REPLACED_CLOSE_CODE,
};
use serde::Serialize;

const TRY_AGAIN_LATER_CLOSE_CODE: u16 = 1013;

#[derive(Clone, Copy)]
pub(super) struct Failure {
    pub diagnostic: BackendError,
    pub code: ProtocolErrorCode,
}

impl Failure {
    pub fn new(diagnostic: BackendError) -> Self {
        let code = match diagnostic {
            BackendError::AuthenticationFailed | BackendError::AuthenticationTimeout => {
                ProtocolErrorCode::AuthenticationFailed
            }
            BackendError::IncompatibleVersion => ProtocolErrorCode::IncompatibleVersion,
            BackendError::InvalidMessage => ProtocolErrorCode::InvalidMessage,
            BackendError::MessageTooLarge => ProtocolErrorCode::MessageTooLarge,
            BackendError::UnexpectedMessage => ProtocolErrorCode::UnexpectedMessage,
            BackendError::StaleGeneration => ProtocolErrorCode::StaleGeneration,
            BackendError::HeartbeatTimeout => ProtocolErrorCode::HeartbeatTimeout,
            BackendError::SessionReplaced => ProtocolErrorCode::SessionReplaced,
            BackendError::Disconnected
            | BackendError::StorageUnavailable
            | BackendError::ServerBusy => ProtocolErrorCode::ServerBusy,
        };
        Self { diagnostic, code }
    }

    fn close_code(self) -> u16 {
        let code = match self.code {
            ProtocolErrorCode::AuthenticationFailed => AUTHENTICATION_FAILURE_CLOSE_CODE,
            ProtocolErrorCode::SessionReplaced => SESSION_REPLACED_CLOSE_CODE,
            ProtocolErrorCode::HeartbeatTimeout | ProtocolErrorCode::ServerBusy => {
                return TRY_AGAIN_LATER_CLOSE_CODE;
            }
            _ => PROTOCOL_FAILURE_CLOSE_CODE,
        };
        code as u16
    }
}

impl From<ContractError> for Failure {
    fn from(error: ContractError) -> Self {
        Self::new(match error {
            ContractError::InvalidMessage => BackendError::InvalidMessage,
            ContractError::MessageTooLarge => BackendError::MessageTooLarge,
            ContractError::IncompatibleVersion => BackendError::IncompatibleVersion,
            ContractError::UnexpectedMessage => BackendError::UnexpectedMessage,
            ContractError::StaleGeneration => BackendError::StaleGeneration,
        })
    }
}

fn protocol_version<Version: TryFrom<i64, Error: std::fmt::Debug>>() -> Version {
    (PROTOCOL_VERSION as i64)
        .try_into()
        .expect("Shared protocol version")
}

pub(super) async fn send(
    socket: &mut (impl Sink<Message> + Unpin),
    value: &impl Serialize,
) -> Result<(), Failure> {
    let text = serde_json::to_string(value).expect("Connector envelope is serializable");
    tokio::time::timeout(
        Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64),
        socket.send(Message::Text(text.into())),
    )
    .await
    .map_err(|_| Failure::new(BackendError::Disconnected))?
    .map_err(|_| Failure::new(BackendError::Disconnected))
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

#[cfg(test)]
mod tests {
    use std::convert::Infallible;
    use std::future::pending;
    use std::time::Duration;

    use futures_util::sink;
    use raicho_protocol::diagnostics_generated::BackendError;
    use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
    use tokio::time::Instant;

    #[tokio::test(start_paused = true)]
    async fn blocked_peer_flush_expires_without_an_unbounded_outgoing_queue() {
        let mut blocked_peer = Box::pin(sink::unfold((), |(), _frame| async {
            pending::<Result<(), Infallible>>().await
        }));
        let started = Instant::now();
        let failure = super::send(&mut blocked_peer, &serde_json::json!({"type": "ping"}))
            .await
            .err()
            .unwrap();
        assert_eq!(failure.diagnostic, BackendError::Disconnected);
        assert_eq!(
            started.elapsed(),
            Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64)
        );
    }
}
