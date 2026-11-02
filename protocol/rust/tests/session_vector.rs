use std::{fs, path::PathBuf};

use raicho_protocol::authentication::{from_hex, to_hex};
use raicho_protocol::canonical_json::canonical_json;
use raicho_protocol::channel::{Channel, Peer, frame_mac, session_key};
use raicho_protocol::{ContractError, Phase};
use serde_json::{Value, json};

fn vector() -> Value {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures/authentication/session.json");
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn peer(name: &Value) -> Peer {
    match name.as_str().unwrap() {
        "server" => Peer::Server,
        _ => Peer::Client,
    }
}

#[test]
fn shared_vector_derives_the_session_key_and_frame_macs() {
    let vector = vector();
    let server_key = from_hex(vector["server_key"].as_str().unwrap()).unwrap();
    let key = session_key(
        &server_key,
        vector["transcript"].as_str().unwrap(),
        vector["generation"].as_str().unwrap(),
    );
    assert_eq!(to_hex(&key), vector["session_key"]);
    for frame in vector["frames"].as_array().unwrap() {
        assert_eq!(canonical_json(&frame["message"]), frame["canonical"]);
        let counter = frame["counter"].as_u64().unwrap();
        let mac = frame_mac(&key, peer(&frame["sender"]), counter, &frame["message"]);
        assert_eq!(to_hex(&mac), frame["mac"]);
    }
    for case in vector["canonical"].as_array().unwrap() {
        assert_eq!(canonical_json(&case["value"]), case["canonical"]);
    }
}

#[test]
fn channels_accept_each_frame_once_in_order_from_the_other_peer() {
    let vector = vector();
    let key = from_hex(vector["session_key"].as_str().unwrap()).unwrap();
    let generation = vector["generation"].as_str().unwrap();
    let frames = vector["frames"].as_array().unwrap();
    let ping = frames[0]["message"].to_string();
    let mut client = Channel::new(key, Peer::Client);
    assert!(client.open(&ping, Phase::ServerControl, generation).is_ok());
    assert_eq!(
        client.open(&ping, Phase::ServerControl, generation).err().unwrap(),
        ContractError::AuthenticationFailed
    );
    let mut server = Channel::new(key, Peer::Server);
    let pong = frames[1]["message"].to_string();
    assert!(server.open(&pong, Phase::ClientControl, generation).is_ok());
    let mut reflected = Channel::new(key, Peer::Server);
    assert_eq!(
        reflected
            .open(&ping.replace("ping", "pong"), Phase::ClientControl, generation)
            .err()
            .unwrap(),
        ContractError::AuthenticationFailed
    );
    let mut sealing = Channel::new(key, Peer::Server);
    let sealed: Value = serde_json::from_str(&sealing.seal(&frames[0]["message"])).unwrap();
    assert_eq!(sealed, frames[0]["message"]);
}

#[test]
fn a_failed_frame_closes_the_channel() {
    let vector = vector();
    let key = from_hex(vector["session_key"].as_str().unwrap()).unwrap();
    let generation = vector["generation"].as_str().unwrap();
    let ping = vector["frames"][0]["message"].clone();
    let mut tampered = ping.clone();
    let mac = ping["mac"].as_str().unwrap();
    let flipped = if mac.starts_with('0') { "1" } else { "0" };
    tampered["mac"] = Value::String(format!("{flipped}{}", &mac[1..]));
    let mut client = Channel::new(key, Peer::Client);
    let mut open = |frame: &Value| client.open(&frame.to_string(), Phase::ServerControl, generation);
    assert_eq!(open(&tampered).err(), Some(ContractError::AuthenticationFailed));
    assert_eq!(open(&ping).err(), Some(ContractError::AuthenticationFailed));
}

#[test]
fn a_frame_without_a_mac_is_invalid() {
    let vector = vector();
    let key = from_hex(vector["session_key"].as_str().unwrap()).unwrap();
    let challenge = json!({"type": "challenge", "protocol_version": 2, "server_nonce": "f".repeat(64)});
    let mut client = Channel::new(key, Peer::Client);
    assert_eq!(
        client
            .open(
                &challenge.to_string(),
                Phase::Challenge,
                vector["generation"].as_str().unwrap()
            )
            .err(),
        Some(ContractError::InvalidMessage)
    );
}
