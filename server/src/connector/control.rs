use std::future::pending;

use raicho_protocol::Phase;
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use tokio::time::{Instant, sleep_until};
use tokio_tungstenite::tungstenite::Utf8Bytes;

use super::handshake::Socket;
use super::heartbeat::Heartbeat;
use super::requests::{Queue, Requests};
use super::{Connector, failure::Failure, transport};

pub(super) async fn run(
    socket: &mut Socket,
    connector: &Connector,
    generation: &Generation,
    channel: &mut Channel,
    queue: &mut Queue,
) -> Failure {
    let mut heartbeat = Heartbeat::new();
    let mut requests = Requests::new();
    loop {
        let has_room = requests.has_room();
        let request_deadline = requests.deadline();
        let result = tokio::select! {
            biased;
            _ = sleep_until(heartbeat.deadline) => heartbeat.send_ping(socket, generation, channel).await,
            _ = expiry(request_deadline) => requests.expire(socket, generation, channel).await,
            received = transport::receive_text(socket) => {
                accept(received, connector, generation, channel, &mut heartbeat, &mut requests)
            },
            Some(exchange) = queue.recv(), if has_room => {
                requests.send(socket, generation, channel, exchange).await
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
