use argon2::password_hash::phc::PasswordHash;
use argon2::password_hash::{PasswordHasher, PasswordVerifier};
use argon2::{Algorithm, Argon2, Params, Version};

use crate::error::{Error, Result};

pub const MINIMUM_PASSWORD_BYTES: usize = 12;
pub const MAXIMUM_PASSWORD_BYTES: usize = 1024;

// OWASP's Argon2id baseline: 19 MiB of memory, two passes, and one lane.
const MEMORY_KIB: u32 = 19_456;
const PASSES: u32 = 2;
const LANES: u32 = 1;

fn hasher() -> Argon2<'static> {
    Argon2::new(
        Algorithm::Argon2id,
        Version::V0x13,
        Params::new(MEMORY_KIB, PASSES, LANES, None).expect("Argon2 parameters are valid"),
    )
}

pub fn validate(password: &[u8]) -> Result<()> {
    if !(MINIMUM_PASSWORD_BYTES..=MAXIMUM_PASSWORD_BYTES).contains(&password.len()) {
        return Err(Error::message("The password must contain 12 to 1024 bytes"));
    }
    Ok(())
}

pub fn hash(password: &[u8]) -> Result<String> {
    validate(password)?;
    let mut salt = [0u8; 16];
    getrandom::fill(&mut salt).map_err(|error| Error::new("Cannot generate a password salt", error))?;
    let hash: PasswordHash = hasher()
        .hash_password_with_salt(password, &salt)
        .map_err(|error| Error::new("Cannot hash the password", error))?;
    Ok(hash.to_string())
}

/// Checks a password against a stored PHC string, using the parameters it records.
pub fn verify(password: &[u8], stored: &str) -> bool {
    password.len() <= MAXIMUM_PASSWORD_BYTES
        && PasswordHash::new(stored).is_ok_and(|hash| hasher().verify_password(password, &hash).is_ok())
}

#[cfg(test)]
mod tests {
    use super::{hash, validate, verify};

    #[test]
    fn a_hash_verifies_only_its_password_and_records_argon2id() {
        let stored = hash(b"correct horse battery").unwrap();
        assert!(stored.starts_with("$argon2id$v=19$m=19456,t=2,p=1$"));
        assert!(verify(b"correct horse battery", &stored));
        assert!(!verify(b"correct horse battery staple", &stored));
        assert!(!verify(b"correct horse battery", "not a hash"));
        assert_ne!(stored, hash(b"correct horse battery").unwrap());
    }

    #[test]
    fn passwords_hold_12_to_1024_bytes() {
        assert!(validate(&[b'a'; 11]).is_err());
        assert!(validate(&[b'a'; 12]).is_ok());
        assert!(validate(&[b'a'; 1024]).is_ok());
        assert!(validate(&[b'a'; 1025]).is_err());
        assert!(hash(b"short").is_err());
    }
}
