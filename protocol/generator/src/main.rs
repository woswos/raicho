use std::{error::Error, fs, path::PathBuf, process::Command};

use serde_json::Value;
use syn::visit_mut::VisitMut;

mod redact;

fn main() -> Result<(), Box<dyn Error>> {
    let protocol = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let output = std::env::args_os()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| protocol.join("rust/src"));
    let schema: Value =
        serde_json::from_slice(&fs::read(protocol.join("schema/connector.schema.json"))?)?;
    check_references(&schema)?;
    let mut types = typify::TypeSpace::default();
    types.add_root_schema(serde_json::from_value(schema)?)?;
    let mut syntax = syn::parse2(types.to_stream())?;
    redact::RemoveDebug.visit_file_mut(&mut syntax);
    fs::create_dir_all(&output)?;
    fs::write(output.join("generated.rs"), prettyplease::unparse(&syntax))?;
    let limits: Value = serde_json::from_slice(&fs::read(protocol.join("limits.json"))?)?;
    fs::write(
        output.join("limits_generated.rs"),
        generate_limits(&limits)?,
    )?;
    let status = Command::new("rustfmt")
        .arg("--config-path")
        .arg(protocol.join("../rustfmt.toml"))
        .arg("--edition=2024")
        .arg(output.join("generated.rs"))
        .arg(output.join("limits_generated.rs"))
        .status()?;
    if !status.success() {
        return Err("Formatting generated Rust bindings failed.".into());
    }
    Ok(())
}

fn check_references(schema: &Value) -> Result<(), Box<dyn Error>> {
    match schema {
        Value::Object(properties) => {
            if let Some(reference) = properties.get("$ref")
                && !reference
                    .as_str()
                    .is_some_and(|value| value.starts_with("#/"))
            {
                return Err("Only local schema references are supported.".into());
            }
            for value in properties.values() {
                check_references(value)?;
            }
        }
        Value::Array(values) => {
            for value in values {
                check_references(value)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn generate_limits(limits: &Value) -> Result<String, Box<dyn Error>> {
    let mut source = String::new();
    for (name, value) in limits.as_object().ok_or("Limits must be an object.")? {
        if !name
            .bytes()
            .all(|value| value.is_ascii_lowercase() || value == b'_')
        {
            return Err("Limit names must use lowercase words and underscores.".into());
        }
        let value = value.as_u64().ok_or("Limits must be unsigned integers.")?;
        source.push_str(&format!(
            "pub const {}: usize = {value};\n",
            name.to_ascii_uppercase()
        ));
    }
    Ok(source)
}

#[cfg(test)]
mod tests {
    use super::{check_references, generate_limits};
    use serde_json::json;

    #[test]
    fn rejects_remote_and_file_references() {
        for reference in [
            "https://example.test/schema",
            "file:///etc/passwd",
            "other.json",
        ] {
            assert!(check_references(&json!({"$ref": reference})).is_err());
        }
        assert!(check_references(&json!({"$ref": "#/definitions/Authenticate"})).is_ok());
    }

    #[test]
    fn emits_sorted_bounded_limit_constants() {
        assert_eq!(
            generate_limits(&json!({"control_max_bytes": 65536, "authentication_max_bytes": 4096}))
                .unwrap(),
            "pub const AUTHENTICATION_MAX_BYTES: usize = 4096;\npub const CONTROL_MAX_BYTES: usize = 65536;\n"
        );
        assert!(generate_limits(&json!({"invalid-name": 1})).is_err());
        assert!(generate_limits(&json!({"negative": -1})).is_err());
    }
}
