mod password;
mod throttle;

use std::time::{Duration, SystemTime, UNIX_EPOCH};

use sha2::{Digest, Sha256};
use tokio::sync::Semaphore;

use crate::persistence::{Database, TokenDigest};
use crate::random::random_hex;

pub use password::{MAXIMUM_PASSWORD_BYTES, hash as hash_password, validate as validate_password};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LoginFailure {
    Unconfigured,
    InvalidPassword,
    Throttled(Duration),
    Unavailable,
}

/// Verifies the deployment password and issues browser sessions.
pub struct Login {
    throttle: throttle::Throttle,
    // Each Argon2 hash holds 19 MiB, so only one runs at a time.
    hashing: Semaphore,
}

impl Default for Login {
    fn default() -> Self {
        Self {
            throttle: throttle::Throttle::default(),
            hashing: Semaphore::new(1),
        }
    }
}

impl Login {
    /// Returns a new session token when the password matches.
    pub async fn sign_in(&self, database: &Database, password: Vec<u8>) -> Result<String, LoginFailure> {
        if let Some(wait) = self.throttle.wait() {
            return Err(LoginFailure::Throttled(wait));
        }
        let stored = database
            .login_password()
            .await
            .map_err(|_| LoginFailure::Unavailable)?
            .ok_or(LoginFailure::Unconfigured)?;
        let verified = {
            let _permit = self.hashing.acquire().await.map_err(|_| LoginFailure::Unavailable)?;
            tokio::task::spawn_blocking(move || password::verify(&password, &stored))
                .await
                .map_err(|_| LoginFailure::Unavailable)?
        };
        if !verified {
            self.throttle.fail();
            return Err(LoginFailure::InvalidPassword);
        }
        self.throttle.succeed();
        let token = random_hex::<32>().map_err(|_| LoginFailure::Unavailable)?;
        database
            .create_browser_session(&digest(&token), now())
            .await
            .map_err(|_| LoginFailure::Unavailable)?;
        Ok(token)
    }
}

/// A session token is 64 lowercase hexadecimal characters, as `sign_in` creates it.
pub fn is_token(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
}

pub fn digest(token: &str) -> TokenDigest {
    Sha256::digest(token.as_bytes()).into()
}

pub fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |elapsed| elapsed.as_secs().try_into().unwrap_or(i64::MAX))
}
