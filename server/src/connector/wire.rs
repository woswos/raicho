use futures_util::SinkExt;
use raicho_protocol::channel::Channel;
use raicho_protocol::contract_generated::{
    Capabilities, Challenge, ChallengeType, Generation, Nonce, Ping, PingType, ProtocolError, ProtocolErrorType,
    Signature, Welcome, WelcomeType,
};
use raicho_protocol::limits_generated::PROTOCOL_VERSION;
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::tungstenite::protocol::{CloseFrame, frame::coding::CloseCode};

use super::failure::Failure;
use super::handshake::Socket;
use super::transport::{WRITE_TIMEOUT, send, send_text};

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
    socket: &mut Socket,
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

pub(super) async fn ping(
    socket: &mut Socket,
    generation: &Generation,
    sequence: u64,
    channel: &mut Channel,
) -> Result<(), Failure> {
    let ping = Ping {
        generation: generation.clone(),
        mac: Channel::unsealed(),
        protocol_version: protocol_version(),
        sequence: sequence.try_into().expect("Positive heartbeat sequence"),
        type_: PingType::Ping,
    };
    send_text(socket, channel.seal(&ping)).await
}

pub(super) async fn terminate(socket: &mut Socket, session: Option<(&Generation, &mut Channel)>, failure: Failure) {
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
        if send_text(socket, text).await.is_ok() {
            let _ = socket
                .send(Message::Close(Some(CloseFrame {
                    code: CloseCode::from(failure.close_code()),
                    reason: failure.code().to_string().into(),
                })))
                .await;
        }
    })
    .await;
}
