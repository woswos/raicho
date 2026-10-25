use std::time::Duration;

use axum::extract::ws::WebSocket;
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use raicho_protocol::{Phase, decode_frame};
use tokio::sync::watch;

use crate::credentials::Credential;
use crate::persistence::CredentialStore;

use super::{Connector, failure::Failure, transport};

pub(super) async fn authenticate(
    socket: &mut WebSocket,
    connector: &Connector,
) -> Result<(Generation, watch::Receiver<bool>), Failure> {
    let deadline = Duration::from_millis(AUTHENTICATION_DEADLINE_MS as u64);
    let message = tokio::time::timeout(deadline, transport::receive_text(socket))
        .await
        .map_err(|_| Failure::new(BackendError::AuthenticationTimeout))??;
    let decoded = decode_frame(&message, Phase::Authentication, None)?;
    let ConnectorMessage::Authenticate(authentication) = decoded else {
        return Err(Failure::new(BackendError::UnexpectedMessage));
    };
    if authentication.backend_kind.as_str() != "thunderbird" {
        return Err(Failure::new(BackendError::InvalidMessage));
    }
    let credential = Credential::parse(&authentication.token)
        .map_err(|_| Failure::new(BackendError::AuthenticationFailed))?;
    let verified = tokio::time::timeout(
        deadline,
        CredentialStore::new(&connector.database).verify(&credential),
    )
    .await
    .map_err(|_| Failure::new(BackendError::StorageUnavailable))?
    .map_err(|_| Failure::new(BackendError::StorageUnavailable))?;
    if !verified {
        return Err(Failure::new(BackendError::AuthenticationFailed));
    }
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).map_err(|_| Failure::new(BackendError::ServerBusy))?;
    let generation: Generation = bytes
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>()
        .parse()
        .map_err(|_| Failure::new(BackendError::ServerBusy))?;
    let replacement = connector
        .register(generation.clone())
        .ok_or(Failure::new(BackendError::ServerBusy))?;
    Ok((generation, replacement))
}
