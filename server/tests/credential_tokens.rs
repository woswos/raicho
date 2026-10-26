use raicho_server::credentials::Credential;
use serde_json::Value;

#[test]
fn tokens_follow_the_shared_connector_configuration_rules() {
    let rules: Value =
        serde_json::from_str(include_str!("../../protocol/fixtures/configuration/connector.json")).unwrap();
    for token in rules["tokens"]["valid"].as_array().unwrap() {
        assert!(Credential::parse(token.as_str().unwrap()).is_ok(), "{token}");
    }
    for token in rules["tokens"]["invalid"].as_array().unwrap() {
        assert!(Credential::parse(token.as_str().unwrap()).is_err(), "{token}");
    }
}
