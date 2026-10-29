use std::error::Error;

use serde_json::Value;

pub fn generate(limits: &Value) -> Result<String, Box<dyn Error>> {
    let mut entries: Vec<_> = limits.as_object().ok_or("Limits must be an object.")?.iter().collect();
    entries.sort_unstable_by(|left, right| left.0.cmp(right.0));
    let mut source = String::new();
    for (name, value) in entries {
        let value = value.as_u64().ok_or("Limits must be unsigned integers.")?;
        source.push_str(&format!("pub const {}: usize = {value};\n", name.to_ascii_uppercase()));
    }
    Ok(source)
}

#[cfg(test)]
mod tests {
    use super::generate;
    use serde_json::json;

    #[test]
    fn emits_sorted_limit_constants() {
        assert_eq!(
            generate(&json!({"maximum_control_bytes": 65536, "maximum_authentication_bytes": 4096})).unwrap(),
            "pub const MAXIMUM_AUTHENTICATION_BYTES: usize = 4096;\npub const MAXIMUM_CONTROL_BYTES: usize = 65536;\n"
        );
    }
}
