mod live_check;
mod token_directory;
mod token_file;

use raicho_protocol::authentication::ConnectorKeys;
use subtle::ConstantTimeEq;

use crate::error::{Error, Result};

const TOKEN_HEX_LENGTH: usize = 64;

pub use live_check::wait_for_connector;
pub use token_directory::{TokenOperation, TokenState, operate_token_directory};
pub use token_file::{Owner, SERVICE_OWNER};

fn is_canonical_token(value: &str) -> bool {
    value.len() == TOKEN_HEX_LENGTH
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

pub struct Credential {
    keys: ConnectorKeys,
}

impl Credential {
    pub fn parse(value: &str) -> Result<Self> {
        if !is_canonical_token(value) {
            return Err(Error::message(
                "Connector token must contain 64 lowercase hexadecimal characters",
            ));
        }
        Ok(Self {
            keys: ConnectorKeys::derive(value),
        })
    }

    pub(crate) fn stored_key(&self) -> &[u8] {
        &self.keys.stored_key
    }

    pub(crate) fn server_key(&self) -> &[u8] {
        &self.keys.server_key
    }

    pub(crate) fn matches(&self, stored_key: &[u8]) -> bool {
        bool::from(self.keys.stored_key.as_slice().ct_eq(stored_key))
    }
}

#[cfg(test)]
mod tests {
    use super::Credential;

    #[test]
    fn credentials_are_canonical_and_errors_never_include_the_input() {
        assert!(Credential::parse(&"0123456789abcdef".repeat(4)).is_ok());
        for value in [
            "a".repeat(63),
            "A".repeat(64),
            "g".repeat(64),
            "a".repeat(65),
            format!("{}\n", "a".repeat(64)),
        ] {
            let error = Credential::parse(&value).err().unwrap().to_string();
            assert!(!error.contains(&value));
        }
    }

    #[test]
    fn credentials_compare_by_stored_key_only() {
        let credential = Credential::parse(&"a".repeat(64)).unwrap();
        assert!(credential.matches(credential.stored_key()));
        assert!(!credential.matches(credential.server_key()));
        assert!(!credential.matches(Credential::parse(&"b".repeat(64)).unwrap().stored_key()));
    }
}
