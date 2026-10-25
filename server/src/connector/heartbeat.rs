use std::time::Duration;

use axum::extract::ws::WebSocket;
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS};
use raicho_protocol::{Phase, decode_frame};
use tokio::time::Instant;

use super::{
    Connector, transport,
    wire::{self, Failure},
};

pub(super) async fn run(
    socket: &mut WebSocket,
    connector: &Connector,
    generation: &Generation,
) -> Failure {
    let mut next_sequence = 1u64;
    let mut outstanding = None;
    let mut deadline = Instant::now() + Duration::from_millis(HEARTBEAT_INTERVAL_MS as u64);
    loop {
        tokio::select! {
            biased;
            _ = tokio::time::sleep_until(deadline) => {
                if outstanding.is_some() { return Failure::new(BackendError::HeartbeatTimeout); }
                if next_sequence > i32::MAX as u64 { return Failure::new(BackendError::ServerBusy); }
                if let Err(error) = wire::ping(socket, generation, next_sequence).await { return error; }
                outstanding = Some(next_sequence);
                next_sequence += 1;
                deadline = Instant::now() + Duration::from_millis(HEARTBEAT_TIMEOUT_MS as u64);
            },
            received = transport::receive_text(socket) => {
                let text = match received {
                    Ok(text) => text,
                    Err(error) => return error,
                };
                let decoded = match decode_frame(&text, Phase::ClientControl, Some(generation)) {
                    Ok(message) => message,
                    Err(error) => return error.into(),
                };
                let ConnectorMessage::Pong(pong) = decoded else { return Failure::new(BackendError::UnexpectedMessage); };
                if outstanding != Some(pong.sequence.get()) { return Failure::new(BackendError::UnexpectedMessage); }
                if !connector.heartbeat(generation) { return Failure::new(BackendError::SessionReplaced); }
                outstanding = None;
                deadline = Instant::now() + Duration::from_millis(HEARTBEAT_INTERVAL_MS as u64);
            },
        }
    }
}
