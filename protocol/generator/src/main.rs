use std::{
    error::Error,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

use serde_json::Value;
use syn::visit_mut::VisitMut;

mod diagnostics;
mod limits;
mod remove_debug;

const CONTRACT: &str = "schema/connector.schema.json";
const LIMITS: &str = "limits.json";
const DIAGNOSTICS: &str = "diagnostics.json";

fn main() -> Result<(), Box<dyn Error>> {
    let output = PathBuf::from(std::env::args_os().nth(1).ok_or("Supply the Rust output directory.")?);
    write_bindings(&output)
}

fn write_bindings(output: &Path) -> Result<(), Box<dyn Error>> {
    let protocol = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let read = |origin: &str| -> Result<Value, Box<dyn Error>> {
        Ok(serde_json::from_slice(&fs::read(protocol.join(origin))?)?)
    };
    let mut types = typify::TypeSpace::default();
    types.add_root_schema(serde_json::from_value(read(CONTRACT)?)?)?;
    let mut syntax = syn::parse2(types.to_stream())?;
    remove_debug::RemoveDebug.visit_file_mut(&mut syntax);
    fs::create_dir_all(output)?;
    let files = [
        ("contract_generated.rs", CONTRACT, prettyplease::unparse(&syntax)),
        ("limits_generated.rs", LIMITS, limits::generate(&read(LIMITS)?)?),
        (
            "diagnostics_generated.rs",
            DIAGNOSTICS,
            diagnostics::generate(&read(DIAGNOSTICS)?)?,
        ),
    ];
    let mut formatter = Command::new("rustfmt");
    formatter
        .arg("--config-path")
        .arg(protocol.join("../rustfmt.toml"))
        .arg("--edition=2024");
    for (name, origin, source) in files {
        fs::write(
            output.join(name),
            format!("// Generated from protocol/{origin}.\n{source}"),
        )?;
        formatter.arg(output.join(name));
    }
    if !formatter.status()?.success() {
        return Err("Formatting generated Rust bindings failed.".into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::{fs, path::Path};

    use super::write_bindings;

    #[test]
    fn writes_the_committed_bindings() {
        let output = tempfile::tempdir().unwrap();
        write_bindings(output.path()).unwrap();
        let committed = Path::new(env!("CARGO_MANIFEST_DIR")).join("../rust/src");
        for name in [
            "contract_generated.rs",
            "limits_generated.rs",
            "diagnostics_generated.rs",
        ] {
            assert_eq!(
                fs::read_to_string(output.path().join(name)).unwrap(),
                fs::read_to_string(committed.join(name)).unwrap(),
                "{name}"
            );
        }
    }
}
