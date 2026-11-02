use std::collections::HashMap;
use std::time::Duration;

use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{Generation, Operation, Outcome, Reply};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{MAXIMUM_PENDING_REQUESTS, MAXIMUM_WIRE_INTEGER, REQUEST_TIMEOUT_MS};
use tokio::sync::{mpsc, oneshot};
use tokio::time::Instant;

use super::handshake::Socket;
use super::{Connector, failure::Failure, wire};

pub const REQUEST_TIMEOUT: Duration = Duration::from_millis(REQUEST_TIMEOUT_MS as u64);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RequestFailure {
    Disconnected,
    StaleGeneration,
    Busy,
    Timeout,
}

pub(super) struct Exchange {
    operation: Operation,
    reply: oneshot::Sender<Result<Outcome, RequestFailure>>,
}

pub(super) type Queue = mpsc::Receiver<Exchange>;

pub(super) fn queue() -> (mpsc::Sender<Exchange>, Queue) {
    mpsc::channel(MAXIMUM_PENDING_REQUESTS)
}

struct Pending {
    reply: oneshot::Sender<Result<Outcome, RequestFailure>>,
    deadline: Instant,
}

// Only the session task writes to the socket, so it owns every request still awaiting a reply.
pub(super) struct Requests {
    next_identifier: u64,
    pending: HashMap<u64, Pending>,
}

impl Requests {
    pub fn new() -> Self {
        Self {
            next_identifier: 1,
            pending: HashMap::new(),
        }
    }

    pub fn has_room(&self) -> bool {
        self.pending.len() < MAXIMUM_PENDING_REQUESTS
    }

    pub fn deadline(&self) -> Option<Instant> {
        self.pending.values().map(|pending| pending.deadline).min()
    }

    pub async fn send(
        &mut self,
        socket: &mut Socket,
        generation: &Generation,
        channel: &mut Channel,
        exchange: Exchange,
    ) -> Result<(), Failure> {
        if exchange.reply.is_closed() {
            return Ok(());
        }
        if self.next_identifier > MAXIMUM_WIRE_INTEGER as u64 {
            let _ = exchange.reply.send(Err(RequestFailure::Busy));
            return Err(Failure::new(BackendError::ServerBusy));
        }
        let identifier = self.next_identifier;
        self.next_identifier += 1;
        wire::request(socket, generation, identifier, exchange.operation, channel).await?;
        self.pending.insert(
            identifier,
            Pending {
                reply: exchange.reply,
                deadline: Instant::now() + REQUEST_TIMEOUT,
            },
        );
        Ok(())
    }

    pub async fn expire(
        &mut self,
        socket: &mut Socket,
        generation: &Generation,
        channel: &mut Channel,
    ) -> Result<(), Failure> {
        let now = Instant::now();
        let expired: Vec<u64> = self
            .pending
            .iter()
            .filter(|(_, pending)| pending.deadline <= now)
            .map(|(identifier, _)| *identifier)
            .collect();
        for identifier in expired {
            if let Some(pending) = self.pending.remove(&identifier) {
                let _ = pending.reply.send(Err(RequestFailure::Timeout));
            }
            wire::cancel(socket, generation, identifier, channel).await?;
        }
        Ok(())
    }

    pub fn complete(&mut self, reply: Reply) -> Result<(), Failure> {
        let identifier = reply.request_id.get();
        match self.pending.remove(&identifier) {
            Some(pending) => {
                let _ = pending.reply.send(Ok(reply.result));
                Ok(())
            }
            // A reply can still arrive after its request expired and was cancelled.
            None if identifier < self.next_identifier => Ok(()),
            None => Err(Failure::new(BackendError::UnexpectedMessage)),
        }
    }
}

impl Connector {
    /// Sends one operation over the active session, which must match `generation` when given.
    pub async fn request(
        &self,
        generation: Option<&Generation>,
        operation: Operation,
    ) -> Result<(Generation, Outcome), RequestFailure> {
        let (sender, active) = {
            let state = self.state.lock().expect("Connector state lock poisoned");
            let active = state.active.as_ref().ok_or(RequestFailure::Disconnected)?;
            if generation.is_some_and(|expected| *expected != active.generation) {
                return Err(RequestFailure::StaleGeneration);
            }
            (active.requests.clone(), active.generation.clone())
        };
        let (reply, receiver) = oneshot::channel();
        sender
            .try_send(Exchange { operation, reply })
            .map_err(|error| match error {
                mpsc::error::TrySendError::Full(_) => RequestFailure::Busy,
                mpsc::error::TrySendError::Closed(_) => RequestFailure::Disconnected,
            })?;
        // The session answers every request it sent by its deadline, so this bound covers only a queued one.
        match tokio::time::timeout(2 * REQUEST_TIMEOUT, receiver).await {
            Ok(Ok(result)) => result.map(|outcome| (active, outcome)),
            Ok(Err(_)) => Err(RequestFailure::Disconnected),
            Err(_) => Err(RequestFailure::Timeout),
        }
    }
}
