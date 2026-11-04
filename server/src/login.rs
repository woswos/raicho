mod password;
mod throttle;

use std::sync::Arc;
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
    throttle: Arc<throttle::Throttle>,
    // Each Argon2 hash holds 19 MiB, so only one runs at a time. The permit also
    // covers the throttle check and update, so concurrent attempts cannot all pass it.
    // The blocking task owns it, so a dropped request neither frees it early nor skips the throttle.
    hashing: Arc<Semaphore>,
}

impl Default for Login {
    fn default() -> Self {
        Self {
            throttle: Arc::default(),
            hashing: Arc::new(Semaphore::new(1)),
        }
    }
}

impl Login {
    /// Returns a new session token when the password matches.
    pub async fn sign_in(&self, database: &Database, password: Vec<u8>) -> Result<String, LoginFailure> {
        let stored = database
            .login_password()
            .await
            .map_err(|_| LoginFailure::Unavailable)?
            .ok_or(LoginFailure::Unconfigured)?;
        let permit = Arc::clone(&self.hashing)
            .acquire_owned()
            .await
            .map_err(|_| LoginFailure::Unavailable)?;
        if let Some(wait) = self.throttle.wait() {
            return Err(LoginFailure::Throttled(wait));
        }
        let throttle = Arc::clone(&self.throttle);
        let verified = tokio::task::spawn_blocking(move || {
            let _permit = permit;
            let verified = password::verify(&password, &stored);
            if verified {
                throttle.succeed();
            } else {
                throttle.fail();
            }
            verified
        })
        .await
        .map_err(|_| LoginFailure::Unavailable)?;
        if !verified {
            return Err(LoginFailure::InvalidPassword);
        }
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

#[cfg(test)]
mod tests {
    use std::pin::pin;

    use tempfile::tempdir;

    use super::throttle::MAXIMUM_FAILURES;
    use super::{Login, LoginFailure, now, password};
    use crate::persistence::Database;

    #[tokio::test]
    async fn an_attempt_dropped_mid_hash_keeps_the_permit_and_still_counts() {
        let directory = tempdir().unwrap();
        let database = Database::open(directory.path()).await.unwrap();
        let stored = password::hash(b"right password!").unwrap();
        database.set_login_password(&stored, now()).await.unwrap();
        let login = Login::default();
        for _ in 0..MAXIMUM_FAILURES {
            {
                let mut attempt = pin!(login.sign_in(&database, b"wrong password!".to_vec()));
                while login.hashing.available_permits() == 1 {
                    assert!(futures_util::poll!(attempt.as_mut()).is_pending());
                    tokio::task::yield_now().await;
                }
            }
            drop(login.hashing.acquire().await.unwrap());
        }
        assert!(matches!(
            login.sign_in(&database, b"right password!".to_vec()).await,
            Err(LoginFailure::Throttled(_))
        ));
    }
}
