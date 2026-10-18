use serde_json::Value;

use crate::{
    ContractError,
    limits_generated::{MAXIMUM_JSON_DEPTH, PROTOCOL_VERSION},
};

pub fn check_values(message: &Value) -> Result<(), ContractError> {
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

pub fn check_version(message: &Value) -> Result<(), ContractError> {
    if let Some(version) = message["protocol_version"].as_f64()
        && version.fract() == 0.0
        && (1.0..=2_147_483_647.0).contains(&version)
        && version != PROTOCOL_VERSION as f64
    {
        return Err(ContractError::IncompatibleVersion);
    }
    Ok(())
}

pub fn normalize_numbers(message: &mut Value) {
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
