use raicho_protocol::authentication::{
    authentication_message, from_hex, server_signature, to_hex, verify_client_proof,
};
use raicho_protocol::channel::{Channel, Peer, session_key};
use raicho_protocol::contract_generated::{ConnectorMessage, Generation, Nonce, Signature};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::{Phase, decode_frame};
use tokio::sync::watch;
use tokio::time::{Instant, timeout_at};

use super::handshake::Socket;
use super::{BACKEND_KIND, Connector, failure::Failure, transport, wire};

pub(super) struct Authenticated {
    pub generation: Generation,
    pub replaced: watch::Receiver<bool>,
    pub server_signature: Signature,
    pub channel: Channel,
}

pub(super) async fn authenticate(
    socket: &mut Socket,
    connector: &Connector,
    deadline: Instant,
) -> Result<Authenticated, Failure> {
    let timed_out = |_| Failure::new(BackendError::AuthenticationTimeout);
    let server_nonce: Nonce = random_hex::<32, _>()?;
    timeout_at(deadline, wire::challenge(socket, &server_nonce))
        .await
        .map_err(timed_out)??;
    let message = timeout_at(deadline, transport::receive_text(socket))
        .await
        .map_err(timed_out)??;
    let decoded = decode_frame(&message, Phase::Authentication, None)?;
    let ConnectorMessage::Authenticate(authentication) = decoded else {
        return Err(Failure::new(BackendError::UnexpectedMessage));
    };
    if authentication.backend_kind.as_str() != BACKEND_KIND {
        return Err(Failure::new(BackendError::InvalidMessage));
    }
    let keys = timeout_at(deadline, connector.database.active_connector_keys())
        .await
        .map_err(|_| Failure::new(BackendError::StorageUnavailable))?
        .map_err(|_| Failure::new(BackendError::StorageUnavailable))?
        .ok_or(Failure::new(BackendError::AuthenticationFailed))?;
    let transcript = authentication_message(&server_nonce, &authentication);
    let proof = from_hex(&authentication.client_proof).ok_or(Failure::new(BackendError::InvalidMessage))?;
    if !verify_client_proof(&keys.stored_key, &transcript, &proof) {
        return Err(Failure::new(BackendError::AuthenticationFailed));
    }
    let server_signature = to_hex(&server_signature(&keys.server_key, &transcript))
        .parse()
        .map_err(|_| Failure::new(BackendError::ServerBusy))?;
    let generation: Generation = random_hex::<16, _>()?;
    let channel = Channel::new(session_key(&keys.server_key, &transcript, &generation), Peer::Server);
    let replaced = connector
        .register(generation.clone())
        .ok_or(Failure::new(BackendError::ServerBusy))?;
    Ok(Authenticated {
        generation,
        replaced,
        server_signature,
        channel,
    })
}

fn random_hex<const BYTES: usize, Value: std::str::FromStr>() -> Result<Value, Failure> {
    let mut bytes = [0u8; BYTES];
    getrandom::fill(&mut bytes).map_err(|_| Failure::new(BackendError::ServerBusy))?;
    bytes
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>()
        .parse()
        .map_err(|_| Failure::new(BackendError::ServerBusy))
}
