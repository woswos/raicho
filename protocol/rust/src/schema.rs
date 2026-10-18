use std::sync::LazyLock;

use serde_json::Value;

use crate::ContractError;

static VALIDATOR: LazyLock<Result<jsonschema::Validator, ()>> = LazyLock::new(|| {
    let schema: Value =
        serde_json::from_str(include_str!("../../schema/connector.schema.json")).map_err(|_| ())?;
    jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .offline()
        .build(&schema)
        .map_err(|_| ())
});

pub fn validate(message: &Value) -> Result<(), ContractError> {
    let validator = VALIDATOR
        .as_ref()
        .map_err(|_| ContractError::InvalidMessage)?;
    if validator.is_valid(message) {
        Ok(())
    } else {
        Err(ContractError::InvalidMessage)
    }
}

#[cfg(test)]
mod tests {
    use super::VALIDATOR;
    use serde_json::json;

    #[test]
    fn embedded_contract_compiles_without_reference_retrieval() {
        assert!(VALIDATOR.is_ok());
        for reference in ["https://example.test/schema", "file:///etc/passwd"] {
            assert!(
                jsonschema::options()
                    .offline()
                    .build(&json!({"$ref": reference}))
                    .is_err()
            );
        }
    }
}
