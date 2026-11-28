use futures_util::{Sink, SinkExt};
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{
    Cancel, CancelType, Capabilities, Challenge, ChallengeType, Generation, Nonce, Operation, Ping, PingType,
    ProtocolError, ProtocolErrorType, Request, RequestId, RequestType, Signature, Welcome, WelcomeType,
};
use raicho_protocol::limits_generated::PROTOCOL_VERSION;
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::tungstenite::protocol::{CloseFrame, frame::coding::CloseCode};

use super::failure::Failure;
use super::handshake::Socket;
use super::transport::{WRITE_TIMEOUT, send};

fn protocol_version<Version: TryFrom<i64, Error: std::fmt::Debug>>() -> Version {
    (PROTOCOL_VERSION as i64).try_into().expect("Shared protocol version")
}

pub(super) async fn challenge(socket: &mut Socket, server_nonce: &Nonce) -> Result<(), Failure> {
    send(
        socket,
        &Challenge {
            protocol_version: protocol_version(),
            server_nonce: server_nonce.clone(),
            type_: ChallengeType::Challenge,
        },
    )
    .await
}

pub(super) async fn welcome(
    socket: &mut (impl Sink<Message> + Unpin),
    generation: &Generation,
    server_signature: &Signature,
) -> Result<(), Failure> {
    send(
        socket,
        &Welcome {
            capabilities: Capabilities(Vec::new()),
            generation: generation.clone(),
            server_signature: server_signature.clone(),
            protocol_version: protocol_version(),
            type_: WelcomeType::Welcome,
        },
    )
    .await
}

pub(super) fn ping(generation: &Generation, sequence: u64, channel: &mut Channel) -> String {
    let ping = Ping {
        generation: generation.clone(),
        mac: Channel::unsealed(),
        protocol_version: protocol_version(),
        sequence: sequence.try_into().expect("Positive heartbeat sequence"),
        type_: PingType::Ping,
    };
    channel.seal(&ping)
}

pub(super) fn request(generation: &Generation, identifier: u64, operation: Operation, channel: &mut Channel) -> String {
    let request = Request {
        generation: generation.clone(),
        mac: Channel::unsealed(),
        operation,
        protocol_version: protocol_version(),
        request_id: request_identifier(identifier),
        type_: RequestType::Request,
    };
    channel.seal(&request)
}

pub(super) fn cancel(generation: &Generation, identifier: u64, channel: &mut Channel) -> String {
    let cancel = Cancel {
        generation: generation.clone(),
        mac: Channel::unsealed(),
        protocol_version: protocol_version(),
        request_id: request_identifier(identifier),
        type_: CancelType::Cancel,
    };
    channel.seal(&cancel)
}

fn request_identifier(identifier: u64) -> RequestId {
    RequestId(identifier.try_into().expect("Positive request identifier"))
}

/// Sends `queued`, the frames already sealed for the session, ahead of the error frame, so the
/// peer reaches the error frame's MAC counter.
pub(super) async fn terminate(
    socket: &mut (impl Sink<Message> + Unpin),
    session: Option<(&Generation, &mut Channel)>,
    queued: Vec<String>,
    failure: Failure,
) {
    let mut frame = ProtocolError {
        code: failure.code(),
        generation: None,
        mac: None,
        protocol_version: protocol_version(),
        type_: ProtocolErrorType::Error,
    };
    let text = match session {
        Some((generation, channel)) => {
            frame.generation = Some(generation.clone());
            channel.seal(&frame)
        }
        None => serde_json::to_string(&frame).expect("Connector envelope is serializable"),
    };
    let _ = tokio::time::timeout(WRITE_TIMEOUT, async {
        for frame in queued.into_iter().chain([text]) {
            if socket.send(Message::Text(frame.into())).await.is_err() {
                return;
            }
        }
        let _ = socket
            .send(Message::Close(Some(CloseFrame {
                code: CloseCode::from(failure.close_code()),
                reason: failure.code().to_string().into(),
            })))
            .await;
    })
    .await;
}
