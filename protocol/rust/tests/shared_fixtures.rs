use std::{fs, path::PathBuf};

use raicho_protocol::{Phase, decode_frame};
use serde::Deserialize;
use serde_json::Value;

#[derive(Deserialize)]
struct Fixture {
    name: String,
    phase: Phase,
    valid: bool,
    error: Option<String>,
    generation: Option<String>,
    message: Option<Value>,
    raw: Option<String>,
    #[serde(default)]
    padding: usize,
}

#[test]
fn shared_contract_fixtures_agree_with_generated_bindings() {
    let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../fixtures");
    let mut paths: Vec<_> = fs::read_dir(directory)
        .unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| {
            path.extension()
                .is_some_and(|extension| extension == "json")
        })
        .collect();
    paths.sort();
    assert!(!paths.is_empty());
    let mut count = 0;
    for path in paths {
        let fixtures: Vec<Fixture> = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
        for fixture in fixtures {
            count += 1;
            verify_fixture(fixture);
        }
    }
    assert!(
        count > 20,
        "The shared corpus must cover multiple boundaries."
    );
}

fn verify_fixture(fixture: Fixture) {
    let mut raw = fixture
        .raw
        .unwrap_or_else(|| serde_json::to_string(&fixture.message.unwrap()).unwrap());
    raw.push_str(&" ".repeat(fixture.padding));
    match decode_frame(&raw, fixture.phase, fixture.generation.as_deref()) {
        Ok(message) => {
            assert!(fixture.valid, "{} unexpectedly passed", fixture.name);
            let serialized = serde_json::to_string(&message).unwrap();
            assert!(
                decode_frame(&serialized, fixture.phase, fixture.generation.as_deref()).is_ok(),
                "{} failed after generated type serialization",
                fixture.name
            );
        }
        Err(error) => {
            assert!(!fixture.valid, "{} failed: {error}", fixture.name);
            assert_eq!(
                Some(error.code()),
                fixture.error.as_deref(),
                "{}",
                fixture.name
            );
        }
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
