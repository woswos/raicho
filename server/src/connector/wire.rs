use std::time::Duration;

use axum::extract::ws::{CloseFrame, Message, WebSocket};
use futures_util::{Sink, SinkExt};
use raicho_protocol::generated::{
    Capabilities, Generation, Ping, PingType, ProtocolError, ProtocolErrorCode, ProtocolErrorType,
    Welcome, WelcomeType,
};
use raicho_protocol::limits_generated::{
    AUTHENTICATION_DEADLINE_MS, HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS,
};
use serde::Serialize;

#[derive(Clone, Copy)]
pub(super) struct Failure {
    pub diagnostic: &'static str,
    pub code: ProtocolErrorCode,
}

impl Failure {
    pub fn new(diagnostic: &'static str) -> Self {
        let code = match diagnostic {
            "authentication_timeout" => "authentication_failed",
            "disconnected" | "storage_unavailable" => "server_busy",
            value => value,
        }
        .parse()
        .expect("Fixed connector error code");
        Self { diagnostic, code }
    }

    fn close_code(self) -> u16 {
        match self.code {
            ProtocolErrorCode::AuthenticationFailed => 4001,
            ProtocolErrorCode::SessionReplaced => 4003,
            ProtocolErrorCode::HeartbeatTimeout | ProtocolErrorCode::ServerBusy => 1013,
            _ => 4002,
        }
    }
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
    .map_err(|_| Failure::new("disconnected"))?
    .map_err(|_| Failure::new("disconnected"))
}

pub(super) async fn welcome(socket: &mut WebSocket, generation: &str) -> Result<(), Failure> {
    send(
        socket,
        &Welcome {
            capabilities: Capabilities(Vec::new()),
            generation: generation.parse().expect("Random generation is canonical"),
            heartbeat_interval_ms: (HEARTBEAT_INTERVAL_MS as i64)
                .try_into()
                .expect("Shared heartbeat interval"),
            heartbeat_timeout_ms: (HEARTBEAT_TIMEOUT_MS as i64)
                .try_into()
                .expect("Shared heartbeat timeout"),
            protocol_version: 1.try_into().expect("Shared protocol version"),
            type_: WelcomeType::Welcome,
        },
    )
    .await
}

pub(super) async fn ping(
    socket: &mut WebSocket,
    generation: &str,
    sequence: u64,
) -> Result<(), Failure> {
    send(
        socket,
        &Ping {
            generation: generation.parse().expect("Random generation is canonical"),
            protocol_version: 1.try_into().expect("Shared protocol version"),
            sequence: sequence.try_into().expect("Positive heartbeat sequence"),
            type_: PingType::Ping,
        },
    )
    .await
}

pub(super) async fn terminate(socket: &mut WebSocket, generation: Option<&str>, failure: Failure) {
    let generation: Option<Generation> =
        generation.map(|value| value.parse().expect("Canonical generation"));
    let frame = ProtocolError {
        code: failure.code,
        generation,
        protocol_version: 1.try_into().expect("Shared protocol version"),
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
        assert_eq!(failure.diagnostic, "disconnected");
        assert_eq!(
            started.elapsed(),
            Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64)
        );
    }
}
