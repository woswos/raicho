mod secret_file;
mod store;

use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

use crate::error::{Error, Result};

pub use store::{CredentialStatus, CredentialStore};

pub struct Credential {
    digest: [u8; 32],
}

impl Credential {
    pub fn parse(value: &str) -> Result<Self> {
        if value.len() != 64
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(Error::message(
                "Connector credential must contain 64 lowercase hexadecimal characters",
            ));
        }
        Ok(Self {
            digest: Sha256::digest(value.as_bytes()).into(),
        })
    }

    fn matches(&self, digest: &[u8]) -> bool {
        bool::from(self.digest.as_slice().ct_eq(digest))
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
    fn digest_has_a_known_sha256_value() {
        let credential = Credential::parse(&"a".repeat(64)).unwrap();
        assert_eq!(
            credential.digest,
            [
                0xff, 0xe0, 0x54, 0xfe, 0x7a, 0xe0, 0xcb, 0x6d, 0xc6, 0x5c, 0x3a, 0xf9, 0xb6, 0x1d,
                0x52, 0x09, 0xf4, 0x39, 0x85, 0x1d, 0xb4, 0x3d, 0x0b, 0xa5, 0x99, 0x73, 0x37, 0xdf,
                0x15, 0x46, 0x68, 0xeb,
            ]
        );
        assert!(credential.matches(&credential.digest));
        assert!(!credential.matches(&Credential::parse(&"b".repeat(64)).unwrap().digest));
    }
}
