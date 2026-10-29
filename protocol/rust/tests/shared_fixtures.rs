use std::{fs, path::PathBuf};

use raicho_protocol::{Phase, decode_frame};
use serde::Deserialize;
use serde_json::Value;

#[derive(Deserialize)]
struct Fixture {
    name: String,
    phase: String,
    valid: bool,
    error: Option<String>,
    generation: Option<String>,
    message: Option<Value>,
    raw: Option<String>,
    #[serde(default)]
    padding: usize,
}

// The decoder relies on the generated types instead of runtime schema validation,
// so no frame that the schema rejects may decode.
#[test]
fn shared_contract_fixtures_agree_with_the_decoder_and_schema() {
    let schema: Value = serde_json::from_str(include_str!("../../schema/connector.schema.json")).unwrap();
    let validator = jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .offline()
        .build(&schema)
        .unwrap();
    let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures");
    let mut paths: Vec<_> = fs::read_dir(directory)
        .unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.extension().is_some_and(|extension| extension == "json"))
        .collect();
    paths.sort();
    assert!(!paths.is_empty());
    let mut count = 0;
    let mut rejected = 0;
    for path in paths {
        let fixtures: Vec<Fixture> = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
        for fixture in fixtures {
            count += 1;
            let raw = raw_frame(&fixture);
            // Only a frame that parses shows that the schema, not the JSON parser, rejected it.
            let parsed = serde_json::from_str::<Value>(&raw).ok();
            let conforms = parsed.as_ref().is_some_and(|value| validator.is_valid(value));
            rejected += usize::from(parsed.is_some() && !conforms);
            verify_fixture(&fixture, &raw, conforms);
        }
    }
    assert!(count > 20, "The shared corpus must cover multiple boundaries.");
    assert!(
        rejected > 10,
        "The corpus must include parsed frames that violate the schema."
    );
}

fn raw_frame(fixture: &Fixture) -> String {
    let mut raw = fixture
        .raw
        .clone()
        .unwrap_or_else(|| serde_json::to_string(fixture.message.as_ref().unwrap()).unwrap());
    raw.push_str(&" ".repeat(fixture.padding));
    raw
}

fn verify_fixture(fixture: &Fixture, raw: &str, conforms: bool) {
    let phase = fixture_phase(&fixture.phase);
    match decode_frame(raw, phase, fixture.generation.as_deref()) {
        Ok(message) => {
            assert!(fixture.valid, "{} unexpectedly passed", fixture.name);
            assert!(conforms, "{} decodes but violates the schema", fixture.name);
            let serialized = serde_json::to_string(&message).unwrap();
            assert!(
                decode_frame(&serialized, phase, fixture.generation.as_deref()).is_ok(),
                "{} failed after generated type serialization",
                fixture.name
            );
        }
        Err(error) => {
            assert!(!fixture.valid, "{} failed: {error}", fixture.name);
            assert_eq!(Some(error.code()), fixture.error.as_deref(), "{}", fixture.name);
        }
    }
}

fn fixture_phase(name: &str) -> Phase {
    match name {
        "authentication" => Phase::Authentication,
        "challenge" => Phase::Challenge,
        "handshake" => Phase::Handshake,
        "client_control" => Phase::ClientControl,
        "server_control" => Phase::ServerControl,
        other => panic!("Unknown fixture phase {other}"),
    }
}

#[test]
fn decoding_errors_do_not_echo_credentials_or_input() {
    let raw = r#"{"token":"fixture-secret-must-not-appear"}"#;
    let error = match decode_frame(raw, Phase::Authentication, None) {
        Ok(_) => panic!("Invalid authentication unexpectedly passed."),
        Err(error) => error,
    };
    assert_eq!(error.to_string(), "invalid_message");
    assert_eq!(format!("{error:?}"), "InvalidMessage");
}
