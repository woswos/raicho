use std::{fs, path::PathBuf};

use serde_json::Value;

#[test]
fn shared_status_fixtures_agree_with_the_status_schema() {
    let protocol = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let read = |path: &str| -> Value { serde_json::from_slice(&fs::read(protocol.join(path)).unwrap()).unwrap() };
    let status_validator = jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .offline()
        .build(&read("schema/status.schema.json"))
        .unwrap();
    let fixtures = read("fixtures/status/documents.json");
    let fixtures = fixtures.as_array().unwrap();
    assert!(fixtures.len() > 10);
    for fixture in fixtures {
        assert_eq!(
            status_validator.is_valid(&fixture["document"]),
            fixture["valid"].as_bool().unwrap(),
            "{}",
            fixture["name"]
        );
    }
}
