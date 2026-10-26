use serde::Serialize;
use serde_json::Value;
use subtle::ConstantTimeEq;

use crate::authentication::{Key, from_hex, hmac, to_hex};
use crate::contract_generated::{ConnectorMessage, Signature};
use crate::decode_frame::decode_value;
use crate::{ContractError, Phase};

const SESSION_KEY_LABEL: &str = "raicho-connector-session";
const FRAME_LABEL: &str = "raicho-connector-frame";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Peer {
    Server,
    Client,
}

impl Peer {
    const fn label(self) -> &'static str {
        match self {
            Self::Server => "server",
            Self::Client => "client",
        }
    }

    const fn other(self) -> Self {
        match self {
            Self::Server => Self::Client,
            Self::Client => Self::Server,
        }
    }
}

pub fn session_key(server_key: &Key, transcript: &str, generation: &str) -> Key {
    hmac(
        server_key,
        format!("{SESSION_KEY_LABEL}\n{transcript}\n{generation}").as_bytes(),
    )
}

pub fn frame_mac(session_key: &Key, sender: Peer, counter: u64, message: &Value) -> Key {
    let input = format!(
        "{FRAME_LABEL}\n{}\n{counter}\n{}",
        sender.label(),
        canonical_json(message)
    );
    hmac(session_key, input.as_bytes())
}

pub fn canonical_json(message: &Value) -> String {
    let mut output = String::new();
    match message {
        Value::Object(properties) => write_object(
            properties.iter().filter(|(name, _)| name.as_str() != "mac"),
            &mut output,
        ),
        value => write_value(value, &mut output),
    }
    output
}

fn write_value(value: &Value, output: &mut String) {
    match value {
        Value::Object(properties) => write_object(properties.iter(), output),
        Value::Array(values) => {
            output.push('[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                write_value(value, output);
            }
            output.push(']');
        }
        scalar => output.push_str(&scalar.to_string()),
    }
}

fn write_object<'message>(properties: impl Iterator<Item = (&'message String, &'message Value)>, output: &mut String) {
    let mut properties: Vec<_> = properties.collect();
    properties.sort_unstable_by(|left, right| left.0.cmp(right.0));
    output.push('{');
    for (index, (name, value)) in properties.into_iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        output.push_str(&Value::String(name.clone()).to_string());
        output.push(':');
        write_value(value, output);
    }
    output.push('}');
}

pub struct Channel {
    key: Key,
    local: Peer,
    sent: u64,
    received: u64,
}

impl Channel {
    pub fn new(session_key: Key, local: Peer) -> Self {
        Self {
            key: session_key,
            local,
            sent: 0,
            received: 0,
        }
    }

    // Typed messages that require a MAC carry this until `seal` replaces it.
    pub fn unsealed() -> Signature {
        "0".repeat(64).parse().expect("Placeholder MAC matches the schema")
    }

    pub fn seal(&mut self, message: &impl Serialize) -> String {
        let mut message = serde_json::to_value(message).expect("Connector messages are serializable");
        let mac = frame_mac(&self.key, self.local, self.sent, &message);
        self.sent += 1;
        message["mac"] = Value::String(to_hex(&mac));
        message.to_string()
    }

    pub fn open(&mut self, raw: &str, phase: Phase, generation: &str) -> Result<ConnectorMessage, ContractError> {
        let (message, typed) = decode_value(raw, phase, Some(generation))?;
        let received = message["mac"]
            .as_str()
            .and_then(from_hex)
            .ok_or(ContractError::InvalidMessage)?;
        let expected = frame_mac(&self.key, self.local.other(), self.received, &message);
        if !bool::from(expected.ct_eq(&received)) {
            return Err(ContractError::AuthenticationFailed);
        }
        self.received += 1;
        Ok(typed)
    }
}
