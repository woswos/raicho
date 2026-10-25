use std::{error::Error, fs, path::PathBuf, process::Command};

use serde_json::Value;
use syn::visit_mut::VisitMut;

mod remove_debug;

fn main() -> Result<(), Box<dyn Error>> {
    let protocol = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let output = PathBuf::from(
        std::env::args_os()
            .nth(1)
            .ok_or("Supply the Rust output directory.")?,
    );
    let schema: Value =
        serde_json::from_slice(&fs::read(protocol.join("schema/connector.schema.json"))?)?;
    let mut types = typify::TypeSpace::default();
    types.add_root_schema(serde_json::from_value(schema)?)?;
    let mut syntax = syn::parse2(types.to_stream())?;
    remove_debug::RemoveDebug.visit_file_mut(&mut syntax);
    fs::create_dir_all(&output)?;
    let files = [
        ("contract_generated.rs", prettyplease::unparse(&syntax)),
        (
            "limits_generated.rs",
            generate_limits(&serde_json::from_slice(&fs::read(
                protocol.join("limits.json"),
            )?)?)?,
        ),
        (
            "diagnostics_generated.rs",
            generate_diagnostics(&serde_json::from_slice(&fs::read(
                protocol.join("diagnostics.json"),
            )?)?)?,
        ),
    ];
    let mut formatter = Command::new("rustfmt");
    formatter
        .arg("--config-path")
        .arg(protocol.join("../rustfmt.toml"))
        .arg("--edition=2024");
    for (name, source) in files {
        fs::write(output.join(name), source)?;
        formatter.arg(output.join(name));
    }
    if !formatter.status()?.success() {
        return Err("Formatting generated Rust bindings failed.".into());
    }
    Ok(())
}

fn generate_limits(limits: &Value) -> Result<String, Box<dyn Error>> {
    let mut entries: Vec<_> = limits
        .as_object()
        .ok_or("Limits must be an object.")?
        .iter()
        .collect();
    entries.sort_unstable_by(|left, right| left.0.cmp(right.0));
    let mut source = String::new();
    for (name, value) in entries {
        let value = value.as_u64().ok_or("Limits must be unsigned integers.")?;
        source.push_str(&format!(
            "pub const {}: usize = {value};\n",
            name.to_ascii_uppercase()
        ));
    }
    Ok(source)
}

fn generate_diagnostics(diagnostics: &Value) -> Result<String, Box<dyn Error>> {
    let mut source = String::new();
    for (name, key) in [
        ("BackendState", "backend_states"),
        ("BackendError", "backend_errors"),
    ] {
        source.push_str(&format!(
            "#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]\n\
             #[serde(rename_all = \"snake_case\")]\npub enum {name} {{\n"
        ));
        for code in diagnostics[key]
            .as_array()
            .ok_or("Diagnostics must be lists.")?
        {
            let code = code.as_str().ok_or("Diagnostic codes must be strings.")?;
            let variant: String = code
                .split('_')
                .flat_map(|word| {
                    let mut characters = word.chars();
                    characters
                        .next()
                        .map(|first| first.to_ascii_uppercase())
                        .into_iter()
                        .chain(characters)
                })
                .collect();
            source.push_str(&format!("    {variant},\n"));
        }
        source.push_str("}\n\n");
    }
    Ok(source)
}

#[cfg(test)]
mod tests {
    use super::{generate_diagnostics, generate_limits};
    use serde_json::json;

    #[test]
    fn emits_sorted_limit_constants() {
        assert_eq!(
            generate_limits(
                &json!({"maximum_control_bytes": 65536, "maximum_authentication_bytes": 4096})
            )
            .unwrap(),
            "pub const MAXIMUM_AUTHENTICATION_BYTES: usize = 4096;\npub const MAXIMUM_CONTROL_BYTES: usize = 65536;\n"
        );
    }

    #[test]
    fn emits_snake_case_serialized_diagnostic_enums() {
        let source = generate_diagnostics(&json!({
            "backend_states": ["connected"],
            "backend_errors": ["storage_unavailable"],
        }))
        .unwrap();
        assert!(source.contains("pub enum BackendState {\n    Connected,\n}"));
        assert!(source.contains("pub enum BackendError {\n    StorageUnavailable,\n}"));
        assert_eq!(source.matches("rename_all = \"snake_case\"").count(), 2);
    }
}
