use raicho_protocol::{ContractError, Phase, decode_frame};

#[test]
fn rejects_duplicate_members_before_version_or_schema_validation() {
    for raw in [
        r#"{"type":"ping","protocol_version":1,"protocol_version":1,"generation":"0123456789abcdef0123456789abcdef","sequence":1}"#,
        r#"{"type":"ping","protocol_version":1,"generation":"0123456789abcdef0123456789abcdef","sequence":1,"\u0073equence":1}"#,
        r#"{"protocol_version":2,"extra":{"member":1,"member":2}}"#,
        r#"{"protocol_version":2,"extra":[{"member":1,"member":2}]}"#,
    ] {
        let result = decode_frame(
            raw,
            Phase::ServerControl,
            Some("0123456789abcdef0123456789abcdef"),
        );
        assert!(matches!(result, Err(ContractError::InvalidMessage)));
    }
}

#[test]
fn numeric_rounding_uses_binary64_ties_to_even() {
    for (version, valid) in [
        (
            "1.00000000000000011102230246251565404236316680908203125",
            true,
        ),
        (
            "1.00000000000000011102230246251565404236316680908203126",
            false,
        ),
    ] {
        let raw = format!(
            r#"{{"type":"ping","protocol_version":{version},"generation":"0123456789abcdef0123456789abcdef","sequence":1}}"#,
        );
        let result = decode_frame(
            &raw,
            Phase::ServerControl,
            Some("0123456789abcdef0123456789abcdef"),
        );
        assert_eq!(result.is_ok(), valid, "Version rounding differed.");
    }
}
