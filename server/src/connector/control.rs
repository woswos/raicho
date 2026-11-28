use std::future::{pending, ready};

use futures_util::{Sink, Stream};
use raicho_protocol::Phase;
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use tokio::time::{Instant, sleep_until};
use tokio_tungstenite::tungstenite::{Error, Message, Utf8Bytes};

use super::heartbeat::Heartbeat;
use super::outbox::{Outbox, Outgoing};
use super::requests::{Queue, Requests};
use super::transport;
use super::{Connector, failure::Failure};

// Reads in a row before the session checks deadlines and queued requests without waiting.
const CONSECUTIVE_READS: usize = 16;

pub(super) async fn run(
    reader: &mut (impl Stream<Item = Result<Message, Error>> + Unpin),
    connector: &Connector,
    generation: &Generation,
    channel: &mut Channel,
    queue: &mut Queue,
    outbox: &Outbox,
    outgoing: &mut Outgoing<impl Sink<Message> + Unpin>,
) -> Failure {
    let writer = outgoing.write_all();
    tokio::pin!(writer);
    let mut heartbeat = Heartbeat::new();
    let mut requests = Requests::new();
    let mut reads = 0;
    loop {
        let has_room = requests.has_room();
        let request_deadline = requests.deadline();
        let reading = reads < CONSECUTIVE_READS;
        // A frame that arrived while a write was pending is read before any deadline fires. A connector
        // that keeps the socket readable still yields to due deadlines and queued requests.
        let result = tokio::select! {
            biased;
            failure = &mut writer => Err(failure),
            received = transport::receive_text(reader), if reading => {
                reads += 1;
                accept(received, connector, generation, channel, &mut heartbeat, &mut requests)
            },
            _ = sleep_until(heartbeat.deadline) => {
                reads = 0;
                heartbeat.send_ping(outbox, generation, channel)
            },
            _ = expiry(request_deadline) => {
                reads = 0;
                requests.expire(outbox, generation, channel)
            },
            Some(exchange) = queue.recv(), if has_room => {
                reads = 0;
                requests.send(outbox, generation, channel, exchange)
            },
            _ = ready(()), if !reading => {
                reads = 0;
                Ok(())
            },
        };
        if let Err(failure) = result {
            return failure;
        }
    }
}

async fn expiry(deadline: Option<Instant>) {
    match deadline {
        Some(deadline) => sleep_until(deadline).await,
        None => pending().await,
    }
}

fn accept(
    received: Result<Utf8Bytes, Failure>,
    connector: &Connector,
    generation: &Generation,
    channel: &mut Channel,
    heartbeat: &mut Heartbeat,
    requests: &mut Requests,
) -> Result<(), Failure> {
    match channel.open(&received?, Phase::ClientControl, generation)? {
        ConnectorMessage::Pong(pong) => heartbeat.accept(&pong, connector, generation),
        ConnectorMessage::Reply(reply) => requests.complete(reply),
        _ => Err(Failure::new(BackendError::UnexpectedMessage)),
    }
}

#[cfg(test)]
mod tests;
