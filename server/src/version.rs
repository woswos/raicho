pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

pub fn commit() -> &'static str {
    match option_env!("RAICHO_COMMIT") {
        Some(commit) if !commit.is_empty() => commit,
        _ => "unknown",
    }
}
