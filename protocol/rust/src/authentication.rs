use hmac::{Hmac, KeyInit, Mac};
use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

use crate::contract_generated::Authenticate;

pub const KEY_BYTES: usize = 32;
pub type Key = [u8; KEY_BYTES];

const CLIENT_KEY_LABEL: &[u8] = b"raicho connector client key";
const SERVER_KEY_LABEL: &[u8] = b"raicho connector server key";

pub struct ConnectorKeys {
    pub stored_key: Key,
    pub server_key: Key,
}

impl ConnectorKeys {
    pub fn derive(token: &str) -> Self {
        Self {
            stored_key: Sha256::digest(client_key(token)).into(),
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
    let client_key = client_key(token);
    let stored_key: Key = Sha256::digest(client_key).into();
    xor(&client_key, &hmac(&stored_key, message.as_bytes()))
}

pub fn verify_client_proof(stored_key: &Key, message: &str, proof: &Key) -> bool {
    let client_key = xor(proof, &hmac(stored_key, message.as_bytes()));
    let candidate: Key = Sha256::digest(client_key).into();
    bool::from(candidate.ct_eq(stored_key))
}

pub fn server_signature(server_key: &Key, message: &str) -> Key {
    hmac(server_key, message.as_bytes())
}

pub fn to_hex(key: &Key) -> String {
    key.iter().map(|byte| format!("{byte:02x}")).collect()
}

pub fn from_hex(value: &str) -> Option<Key> {
    if value.len() != KEY_BYTES * 2 {
        return None;
    }
    let mut key = [0; KEY_BYTES];
    for (byte, pair) in key.iter_mut().zip(value.as_bytes().chunks(2)) {
        *byte = u8::from_str_radix(std::str::from_utf8(pair).ok()?, 16).ok()?;
    }
    Some(key)
}

fn client_key(token: &str) -> Key {
    hmac(token.as_bytes(), CLIENT_KEY_LABEL)
}

fn hmac(key: &[u8], message: &[u8]) -> Key {
    let mut code = Hmac::<Sha256>::new_from_slice(key).expect("HMAC accepts any key length");
    code.update(message);
    code.finalize().into_bytes().into()
}

fn xor(left: &Key, right: &Key) -> Key {
    std::array::from_fn(|index| left[index] ^ right[index])
}
