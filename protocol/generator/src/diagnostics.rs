use std::error::Error;

use serde_json::Value;

pub fn generate(diagnostics: &Value) -> Result<String, Box<dyn Error>> {
    let mut source = String::new();
    for (name, key) in [("BackendState", "backend_states"), ("BackendError", "backend_errors")] {
        source.push_str(&format!(
            "#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]\n\
             #[serde(rename_all = \"snake_case\")]\npub enum {name} {{\n"
        ));
        for code in codes(diagnostics, key)? {
            source.push_str(&format!("    {},\n", variant(code)));
        }
        source.push_str("}\n\n");
    }
    let contract_errors = codes(diagnostics, "contract_errors")?;
    source.push_str("#[derive(Clone, Copy, Debug, Eq, PartialEq)]\npub enum ContractError {\n");
    for code in &contract_errors {
        source.push_str(&format!("    {},\n", variant(code)));
    }
    source.push_str("}\n\nimpl ContractError {\n    pub const fn code(self) -> &'static str {\n        match self {\n");
    for code in &contract_errors {
        source.push_str(&format!("            Self::{} => \"{code}\",\n", variant(code)));
    }
    source.push_str(
        "        }\n    }\n}\n\n\
         impl std::fmt::Display for ContractError {\n\
         fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {\n\
         formatter.write_str(self.code())\n}\n}\n\n\
         impl std::error::Error for ContractError {}\n",
    );
    Ok(source)
}

fn codes<'diagnostics>(diagnostics: &'diagnostics Value, key: &str) -> Result<Vec<&'diagnostics str>, Box<dyn Error>> {
    diagnostics[key]
        .as_array()
        .ok_or("Diagnostics must be lists.")?
        .iter()
        .map(|code| code.as_str().ok_or_else(|| "Diagnostic codes must be strings.".into()))
        .collect()
}

fn variant(code: &str) -> String {
    code.split('_')
        .flat_map(|word| {
            let mut characters = word.chars();
            characters
                .next()
                .map(|first| first.to_ascii_uppercase())
                .into_iter()
                .chain(characters)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::generate;
    use serde_json::json;

    #[test]
    fn emits_snake_case_serialized_diagnostic_enums() {
        let source = generate(&json!({
            "backend_states": ["connected"],
            "backend_errors": ["storage_unavailable"],
            "contract_errors": ["invalid_message"],
        }))
        .unwrap();
        assert!(source.contains("pub enum BackendState {\n    Connected,\n}"));
        assert!(source.contains("pub enum BackendError {\n    StorageUnavailable,\n}"));
        assert!(source.contains("pub enum ContractError {\n    InvalidMessage,\n}"));
        assert!(source.contains("Self::InvalidMessage => \"invalid_message\","));
        assert_eq!(source.matches("rename_all = \"snake_case\"").count(), 2);
    }
}
