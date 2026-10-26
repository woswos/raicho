use std::{fs, path::PathBuf};

use raicho_protocol::{Phase, decode_frame};
use serde::Deserialize;
use serde_json::Value;

#[derive(Deserialize)]
struct Fixture {
    name: String,
    phase: Phase,
    generation: Option<String>,
    message: Option<Value>,
    raw: Option<String>,
}

fn fixtures() -> Vec<Fixture> {
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
    paths
        .into_iter()
        .flat_map(|path| serde_json::from_slice::<Vec<Fixture>>(&fs::read(path).unwrap()).unwrap())
        .collect()
}

// The decoder relies on the generated types instead of runtime schema validation,
// so no frame that the schema rejects may decode.
#[test]
fn the_decoder_accepts_only_frames_the_schema_accepts() {
    let schema: Value =
        serde_json::from_str(include_str!("../../schema/connector.schema.json")).unwrap();
    let validator = jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .offline()
        .build(&schema)
        .unwrap();
    let mut rejected = 0;
    for fixture in fixtures() {
        let raw = fixture
            .raw
            .unwrap_or_else(|| serde_json::to_string(&fixture.message.unwrap()).unwrap());
        let conforms =
            serde_json::from_str::<Value>(&raw).is_ok_and(|value| validator.is_valid(&value));
        let decodes = decode_frame(&raw, fixture.phase, fixture.generation.as_deref()).is_ok();
        assert!(
            conforms || !decodes,
            "{} decodes but violates the schema",
            fixture.name
        );
        rejected += usize::from(!conforms);
    }
    assert!(
        rejected > 10,
        "The corpus must include frames that violate the schema."
    );
}
