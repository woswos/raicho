use std::time::Duration;

use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{Generation, Pong};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{HEARTBEAT_INTERVAL_MS, HEARTBEAT_TIMEOUT_MS, MAXIMUM_WIRE_INTEGER};
use tokio::time::Instant;

use super::handshake::Socket;
use super::{Connector, failure::Failure, wire};

pub(super) struct Heartbeat {
    next_sequence: u64,
    outstanding: Option<u64>,
    pub deadline: Instant,
}

impl Heartbeat {
    pub fn new() -> Self {
        Self {
            next_sequence: 1,
            outstanding: None,
            deadline: after(HEARTBEAT_INTERVAL_MS),
        }
    }

    pub async fn send_ping(
        &mut self,
        socket: &mut Socket,
        generation: &Generation,
        channel: &mut Channel,
    ) -> Result<(), Failure> {
        if self.outstanding.is_some() {
            return Err(Failure::new(BackendError::HeartbeatTimeout));
        }
        if self.next_sequence > MAXIMUM_WIRE_INTEGER as u64 {
            return Err(Failure::new(BackendError::ServerBusy));
        }
        wire::ping(socket, generation, self.next_sequence, channel).await?;
        self.outstanding = Some(self.next_sequence);
        self.next_sequence += 1;
        self.deadline = after(HEARTBEAT_TIMEOUT_MS);
        Ok(())
    }

    pub fn accept(&mut self, pong: &Pong, connector: &Connector, generation: &Generation) -> Result<(), Failure> {
        if self.outstanding != Some(pong.sequence.get()) {
            return Err(Failure::new(BackendError::UnexpectedMessage));
        }
        if !connector.heartbeat(generation) {
            return Err(Failure::new(BackendError::SessionReplaced));
        }
        self.outstanding = None;
        self.deadline = after(HEARTBEAT_INTERVAL_MS);
        Ok(())
    }
}

fn after(milliseconds: usize) -> Instant {
    Instant::now() + Duration::from_millis(milliseconds as u64)
}
