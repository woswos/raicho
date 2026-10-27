use std::{fs, path::PathBuf};

use raicho_protocol::authentication::{
    ConnectorKeys, authentication_message, client_proof, from_hex, server_signature, to_hex, verify_client_proof,
};
use raicho_protocol::contract_generated::Authenticate;
use serde_json::{Value, json};

fn vector() -> Value {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures/authentication/vector.json");
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

#[test]
fn shared_vector_derives_keys_proof_and_server_signature() {
    let vector = vector();
    let token = vector["token"].as_str().unwrap();
    let authenticate: Authenticate = serde_json::from_value(json!({
        "type": "authenticate",
        "protocol_version": vector["protocol_version"],
        "backend_kind": vector["backend_kind"],
        "backend_version": vector["backend_version"],
        "connector_version": vector["connector_version"],
        "capabilities": vector["capabilities"],
        "client_nonce": vector["client_nonce"],
        "client_proof": vector["client_proof"],
    }))
    .unwrap();
    let message = authentication_message(vector["server_nonce"].as_str().unwrap(), &authenticate);
    assert_eq!(message, vector["message"]);
    let keys = ConnectorKeys::derive(token);
    assert_eq!(to_hex(&keys.stored_key), vector["stored_key"]);
    assert_eq!(to_hex(&keys.server_key), vector["server_key"]);
    let proof = client_proof(token, &message);
    assert_eq!(to_hex(&proof), vector["client_proof"]);
    assert!(verify_client_proof(&keys.stored_key, &message, &proof));
    assert_eq!(
        to_hex(&server_signature(&keys.server_key, &message)),
        vector["server_signature"]
    );
}

#[test]
fn proofs_fail_for_another_token_message_or_altered_byte() {
    let vector = vector();
    let message = vector["message"].as_str().unwrap();
    let keys = ConnectorKeys::derive(vector["token"].as_str().unwrap());
    let proof = from_hex(vector["client_proof"].as_str().unwrap()).unwrap();
    let other = ConnectorKeys::derive(&"f".repeat(64));
    assert!(!verify_client_proof(&other.stored_key, message, &proof));
    assert!(!verify_client_proof(&keys.stored_key, &format!("{message}\n"), &proof));
    let mut altered = proof;
    altered[0] ^= 1;
    assert!(!verify_client_proof(&keys.stored_key, message, &altered));
    assert_eq!(from_hex("0"), None);
    assert_eq!(from_hex(&"g".repeat(64)), None);
    assert_eq!(from_hex(&"A".repeat(64)), None);
    assert_eq!(from_hex(&"+f".repeat(32)), None);
}
