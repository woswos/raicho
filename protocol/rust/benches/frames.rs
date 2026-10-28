use std::hint::black_box;
use std::{fs, path::PathBuf};

use criterion::{Criterion, criterion_group, criterion_main};
use raicho_protocol::authentication::{ConnectorKeys, client_proof, from_hex, verify_client_proof};
use raicho_protocol::channel::{Channel, Peer};
use raicho_protocol::{Phase, decode_frame};
use serde_json::Value;

fn fixture(name: &str) -> Value {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures").join(name);
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn decoding(criterion: &mut Criterion) {
    let authenticate = fixture("handshake.json")[0]["message"].to_string();
    let session = fixture("authentication/session.json");
    let generation = session["generation"].as_str().unwrap();
    let ping = session["frames"][0]["message"].to_string();
    criterion.bench_function("decode authenticate", |bencher| {
        bencher.iter(|| decode_frame(black_box(&authenticate), Phase::Authentication, None).unwrap())
    });
    criterion.bench_function("decode ping", |bencher| {
        bencher.iter(|| decode_frame(black_box(&ping), Phase::ServerControl, Some(generation)).unwrap())
    });
}

fn sealing(criterion: &mut Criterion) {
    let session = fixture("authentication/session.json");
    let key = from_hex(session["session_key"].as_str().unwrap()).unwrap();
    let generation = session["generation"].as_str().unwrap();
    let ping = session["frames"][0]["message"].clone();
    criterion.bench_function("seal and open ping", |bencher| {
        bencher.iter(|| {
            let mut server = Channel::new(key, Peer::Server);
            let mut client = Channel::new(key, Peer::Client);
            let frame = server.seal(black_box(&ping));
            client.open(&frame, Phase::ServerControl, generation).unwrap()
        })
    });
}

fn authentication(criterion: &mut Criterion) {
    let vector = fixture("authentication/vector.json");
    let token = vector["token"].as_str().unwrap();
    let message = vector["message"].as_str().unwrap();
    let keys = ConnectorKeys::derive(token);
    let proof = client_proof(token, message);
    criterion.bench_function("client proof", |bencher| {
        bencher.iter(|| client_proof(black_box(token), black_box(message)))
    });
    criterion.bench_function("verify client proof", |bencher| {
        bencher.iter(|| verify_client_proof(&keys.stored_key, black_box(message), &proof))
    });
}

criterion_group!(frames, decoding, sealing, authentication);
criterion_main!(frames);
