use serde_json::Value;

use crate::{
    ContractError,
    contract_generated::ConnectorMessage,
    limits_generated::{
        MAXIMUM_AUTHENTICATION_BYTES, MAXIMUM_CONTROL_BYTES, MAXIMUM_JSON_DEPTH, PROTOCOL_VERSION,
    },
    raw_json, schema,
};

#[derive(Clone, Copy, Debug, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    Authentication,
    Challenge,
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
        Phase::Authentication => MAXIMUM_AUTHENTICATION_BYTES,
        _ => MAXIMUM_CONTROL_BYTES,
    };
    if raw.len() > maximum {
        return Err(ContractError::MessageTooLarge);
    }
    let mut message = raw_json::parse_message(raw)?;
    check_wire_values(&message)?;
    check_unsupported_version(&message)?;
    schema::validate(&message)?;
    check_phase(&message, phase, generation)?;
    normalize_numbers(&mut message);
    serde_json::from_value(message).map_err(|_| ContractError::InvalidMessage)
}

fn check_wire_values(message: &Value) -> Result<(), ContractError> {
    let mut pending = vec![(message, 0)];
    while let Some((value, depth)) = pending.pop() {
        if depth > MAXIMUM_JSON_DEPTH {
            return Err(ContractError::InvalidMessage);
        }
        match value {
            Value::String(text) if !is_printable_ascii(text) => {
                return Err(ContractError::InvalidMessage);
            }
            Value::Array(values) => pending.extend(values.iter().map(|value| (value, depth + 1))),
            Value::Object(properties) => {
                if !properties.keys().all(|key| is_printable_ascii(key)) {
                    return Err(ContractError::InvalidMessage);
                }
                pending.extend(properties.values().map(|value| (value, depth + 1)));
            }
            _ => {}
        }
    }
    Ok(())
}

fn is_printable_ascii(text: &str) -> bool {
    text.bytes()
        .all(|character| (32..=126).contains(&character))
}

fn check_unsupported_version(message: &Value) -> Result<(), ContractError> {
    if let Some(version) = message["protocol_version"].as_f64()
        && version.fract() == 0.0
        && (1.0..=2_147_483_647.0).contains(&version)
        && version != PROTOCOL_VERSION as f64
    {
        return Err(ContractError::IncompatibleVersion);
    }
    Ok(())
}

fn check_phase(
    message: &Value,
    phase: Phase,
    generation: Option<&str>,
) -> Result<(), ContractError> {
    let message_type = message["type"].as_str();
    let unclaimed_error = message_type == Some("error") && message.get("generation").is_none();
    let permitted = match phase {
        Phase::Authentication => message_type == Some("authenticate"),
        Phase::Challenge => message_type == Some("challenge") || unclaimed_error,
        Phase::Handshake => message_type == Some("welcome") || unclaimed_error,
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

fn normalize_numbers(message: &mut Value) {
    match message {
        Value::Number(number) => {
            if let Some(integer) = number.as_f64()
                && integer.fract() == 0.0
                && (0.0..=2_147_483_647.0).contains(&integer)
            {
                *number = (integer as u64).into();
            }
        }
        Value::Object(properties) => {
            for value in properties.values_mut() {
                normalize_numbers(value);
            }
        }
        Value::Array(values) => {
            for value in values {
                normalize_numbers(value);
            }
        }
        _ => {}
    }
}
