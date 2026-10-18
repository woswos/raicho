use serde_json::Value;

use crate::{
    ContractError,
    generated::ConnectorMessage,
    limits_generated::{AUTHENTICATION_MAX_BYTES, CONTROL_MAX_BYTES},
    parse, preflight, schema,
};

#[derive(Clone, Copy, Debug, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    Authentication,
    Handshake,
    ClientControl,
    ServerControl,
}

pub fn decode_frame(
    raw: &str,
    phase: Phase,
    generation: Option<&str>,
) -> Result<ConnectorMessage, ContractError> {
    let maximum = match phase {
        Phase::Authentication => AUTHENTICATION_MAX_BYTES,
        _ => CONTROL_MAX_BYTES,
    };
    if raw.len() > maximum {
        return Err(ContractError::MessageTooLarge);
    }
    let mut message = parse::parse_message(raw)?;
    preflight::check_values(&message)?;
    preflight::check_version(&message)?;
    schema::validate(&message)?;
    check_phase(&message, phase, generation)?;
    preflight::normalize_numbers(&mut message);
    serde_json::from_value(message).map_err(|_| ContractError::InvalidMessage)
}

fn check_phase(
    message: &Value,
    phase: Phase,
    generation: Option<&str>,
) -> Result<(), ContractError> {
    let message_type = message["type"].as_str();
    let permitted = match phase {
        Phase::Authentication => message_type == Some("authenticate"),
        Phase::Handshake => {
            message_type == Some("welcome")
                || (message_type == Some("error") && message.get("generation").is_none())
        }
        Phase::ClientControl => message_type == Some("pong"),
        Phase::ServerControl => matches!(message_type, Some("ping" | "error")),
    };
    if !permitted {
        return Err(ContractError::UnexpectedMessage);
    }
    if matches!(phase, Phase::ClientControl | Phase::ServerControl)
        && (generation.is_none() || generation != message["generation"].as_str())
    {
        return Err(ContractError::StaleGeneration);
    }
    Ok(())
}
