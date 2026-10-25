use std::time::Duration;

use raicho_protocol::Phase;
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS};
use tokio::time::Instant;
use tokio_tungstenite::tungstenite::Utf8Bytes;

use super::handshake::Socket;
use super::{Connector, failure::Failure, transport, wire};

struct Heartbeat {
    next_sequence: u64,
    outstanding: Option<u64>,
    deadline: Instant,
}

pub(super) async fn run(
    socket: &mut Socket,
    connector: &Connector,
    generation: &Generation,
    channel: &mut Channel,
) -> Failure {
    let mut heartbeat = Heartbeat {
        next_sequence: 1,
        outstanding: None,
        deadline: after(HEARTBEAT_INTERVAL_MS),
    };
    loop {
        let result = tokio::select! {
            biased;
            _ = tokio::time::sleep_until(heartbeat.deadline) => {
                send_ping(socket, generation, channel, &mut heartbeat).await
            },
            received = transport::receive_text(socket) => {
                accept_pong(received, connector, generation, channel, &mut heartbeat)
            },
        };
        if let Err(failure) = result {
            return failure;
        }
    }
}

async fn send_ping(
    socket: &mut Socket,
    generation: &Generation,
    channel: &mut Channel,
    heartbeat: &mut Heartbeat,
) -> Result<(), Failure> {
    if heartbeat.outstanding.is_some() {
        return Err(Failure::new(BackendError::HeartbeatTimeout));
    }
    if heartbeat.next_sequence > i32::MAX as u64 {
        return Err(Failure::new(BackendError::ServerBusy));
    }
    wire::ping(socket, generation, heartbeat.next_sequence, channel).await?;
    heartbeat.outstanding = Some(heartbeat.next_sequence);
    heartbeat.next_sequence += 1;
    heartbeat.deadline = after(HEARTBEAT_TIMEOUT_MS);
    Ok(())
}

fn accept_pong(
    received: Result<Utf8Bytes, Failure>,
    connector: &Connector,
    generation: &Generation,
    channel: &mut Channel,
    heartbeat: &mut Heartbeat,
) -> Result<(), Failure> {
    let text = received?;
    let ConnectorMessage::Pong(pong) = channel.open(&text, Phase::ClientControl, generation)?
    else {
        return Err(Failure::new(BackendError::UnexpectedMessage));
    };
    if heartbeat.outstanding != Some(pong.sequence.get()) {
        return Err(Failure::new(BackendError::UnexpectedMessage));
    }
    if !connector.heartbeat(generation) {
        return Err(Failure::new(BackendError::SessionReplaced));
    }
    heartbeat.outstanding = None;
    heartbeat.deadline = after(HEARTBEAT_INTERVAL_MS);
    Ok(())
}

fn after(milliseconds: usize) -> Instant {
    Instant::now() + Duration::from_millis(milliseconds as u64)
}
