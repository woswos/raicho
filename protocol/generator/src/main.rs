use std::{error::Error, fs, path::PathBuf, process::Command};

use syn::visit_mut::VisitMut;

mod diagnostics;
mod limits;
mod remove_debug;

fn main() -> Result<(), Box<dyn Error>> {
    let protocol = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let output = PathBuf::from(std::env::args_os().nth(1).ok_or("Supply the Rust output directory.")?);
    let mut types = typify::TypeSpace::default();
    types.add_root_schema(serde_json::from_slice(&fs::read(
        protocol.join("schema/connector.schema.json"),
    )?)?)?;
    let mut syntax = syn::parse2(types.to_stream())?;
    remove_debug::RemoveDebug.visit_file_mut(&mut syntax);
    fs::create_dir_all(&output)?;
    let files = [
        (
            "contract_generated.rs",
            "schema/connector.schema.json",
            prettyplease::unparse(&syntax),
        ),
        (
            "limits_generated.rs",
            "limits.json",
            limits::generate(&serde_json::from_slice(&fs::read(protocol.join("limits.json"))?)?)?,
        ),
        (
            "diagnostics_generated.rs",
            "diagnostics.json",
            diagnostics::generate(&serde_json::from_slice(&fs::read(protocol.join("diagnostics.json"))?)?)?,
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
