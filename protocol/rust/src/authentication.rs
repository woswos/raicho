use hmac::{Hmac, KeyInit, Mac};
use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

use crate::contract_generated::Authenticate;

pub const KEY_BYTES: usize = 32;
pub type Key = [u8; KEY_BYTES];

// Every derived key depends on these exact bytes, so changing the label changes every key.
const CONNECTOR_KEY_LABEL: &[u8] = b"raicho connector client key";
const SERVER_KEY_LABEL: &[u8] = b"raicho connector server key";

pub struct ConnectorKeys {
    pub stored_key: Key,
    pub server_key: Key,
}

impl ConnectorKeys {
    pub fn derive(token: &str) -> Self {
        Self {
            stored_key: derive_stored_key(&connector_key(token)),
            server_key: hmac(token.as_bytes(), SERVER_KEY_LABEL),
        }
    }
}

pub fn authentication_message(server_nonce: &str, authenticate: &Authenticate) -> String {
    let mut lines = vec![
        "raicho-connector-authentication".to_owned(),
        authenticate.protocol_version.to_string(),
        server_nonce.to_owned(),
        authenticate.client_nonce.to_string(),
        authenticate.backend_kind.to_string(),
        authenticate.backend_version.to_string(),
        authenticate.connector_version.to_string(),
        authenticate.capabilities.0.len().to_string(),
    ];
    lines.extend(authenticate.capabilities.0.iter().cloned());
    lines.join("\n")
}

pub fn client_proof(token: &str, message: &str) -> Key {
    let connector_key = connector_key(token);
    xor(
        &connector_key,
        &hmac(&derive_stored_key(&connector_key), message.as_bytes()),
    )
}

pub fn verify_client_proof(stored_key: &Key, message: &str, proof: &Key) -> bool {
    let connector_key = xor(proof, &hmac(stored_key, message.as_bytes()));
    bool::from(derive_stored_key(&connector_key).ct_eq(stored_key))
}

pub fn server_signature(server_key: &Key, message: &str) -> Key {
    hmac(server_key, message.as_bytes())
}

pub fn to_hex(key: &Key) -> String {
    key.iter().map(|byte| format!("{byte:02x}")).collect()
}

pub fn from_hex(value: &str) -> Option<Key> {
    if value.len() != KEY_BYTES * 2 || !value.bytes().all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f')) {
        return None;
    }
    let mut key = [0; KEY_BYTES];
    for (byte, pair) in key.iter_mut().zip(value.as_bytes().chunks(2)) {
        *byte = u8::from_str_radix(std::str::from_utf8(pair).ok()?, 16).ok()?;
    }
    Some(key)
}

fn connector_key(token: &str) -> Key {
    hmac(token.as_bytes(), CONNECTOR_KEY_LABEL)
}

fn derive_stored_key(connector_key: &Key) -> Key {
    Sha256::digest(connector_key).into()
}

pub(crate) fn hmac(key: &[u8], message: &[u8]) -> Key {
    let mut code = Hmac::<Sha256>::new_from_slice(key).expect("HMAC accepts any key length");
    code.update(message);
    code.finalize().into_bytes().into()
}

fn xor(left: &Key, right: &Key) -> Key {
    std::array::from_fn(|index| left[index] ^ right[index])
}
