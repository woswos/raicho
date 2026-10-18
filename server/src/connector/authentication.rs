use axum::extract::ws::WebSocket;
use raicho_protocol::generated::ConnectorMessage;
use raicho_protocol::{Phase, decode_frame};
use tokio::sync::watch;

use crate::credentials::{Credential, CredentialStore};

use super::{Connector, transport, wire::Failure};

pub(super) async fn authenticate(
    socket: &mut WebSocket,
    connector: &Connector,
) -> Result<(String, watch::Receiver<bool>), Failure> {
    let message = transport::receive_text(socket).await?;
    let decoded = decode_frame(&message, Phase::Authentication, None)
        .map_err(|error| Failure::new(error.code()))?;
    let ConnectorMessage::Authenticate(authentication) = decoded else {
        return Err(Failure::new("unexpected_message"));
    };
    if authentication.backend_kind.as_str() != "thunderbird" {
        return Err(Failure::new("invalid_message"));
    }
    let credential = Credential::parse(&authentication.token)
        .map_err(|_| Failure::new("authentication_failed"))?;
    if !CredentialStore::new(&connector.database)
        .verify(&credential)
        .await
        .map_err(|_| Failure::new("storage_unavailable"))?
    {
        return Err(Failure::new("authentication_failed"));
    }
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).map_err(|_| Failure::new("server_busy"))?;
    let generation: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();
    let replacement = connector
        .register(generation.clone())
        .ok_or(Failure::new("server_busy"))?;
    Ok((generation, replacement))
}
