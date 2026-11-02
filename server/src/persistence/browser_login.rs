use crate::error::{Error, Result};

use super::Database;

pub const SESSION_IDLE_SECONDS: i64 = 7 * 24 * 60 * 60;
pub const SESSION_LIFETIME_SECONDS: i64 = 30 * 24 * 60 * 60;
pub const SESSION_TOUCH_SECONDS: i64 = 5 * 60;
pub const MAXIMUM_SESSIONS: i64 = 32;

pub type TokenDigest = [u8; 32];

impl Database {
    pub async fn login_password(&self) -> Result<Option<String>> {
        sqlx::query_scalar(include_str!("../../queries/read_login_password.sql"))
            .fetch_optional(self.pool())
            .await
            .map_err(storage_error)
    }

    /// Replaces the password and revokes every session in one transaction.
    pub async fn set_login_password(&self, password_hash: &str, now: i64) -> Result<()> {
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        sqlx::query(include_str!("../../queries/write_login_password.sql"))
            .bind(password_hash)
            .bind(now)
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        sqlx::query(include_str!("../../queries/delete_browser_sessions.sql"))
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn revoke_browser_sessions(&self) -> Result<()> {
        sqlx::query(include_str!("../../queries/delete_browser_sessions.sql"))
            .execute(self.pool())
            .await
            .map_err(storage_error)?;
        Ok(())
    }

    pub async fn browser_session_count(&self) -> Result<i64> {
        sqlx::query_scalar(include_str!("../../queries/count_browser_sessions.sql"))
            .fetch_one(self.pool())
            .await
            .map_err(storage_error)
    }

    /// Stores a new session, after removing expired ones and the oldest beyond the limit.
    pub async fn create_browser_session(&self, digest: &TokenDigest, now: i64) -> Result<()> {
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        sqlx::query(include_str!("../../queries/delete_expired_browser_sessions.sql"))
            .bind(now)
            .bind(now - SESSION_IDLE_SECONDS)
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        sqlx::query(include_str!("../../queries/delete_oldest_browser_sessions.sql"))
            .bind(MAXIMUM_SESSIONS - 1)
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        sqlx::query(include_str!("../../queries/insert_browser_session.sql"))
            .bind(digest.as_slice())
            .bind(now)
            .bind(now)
            .bind(now + SESSION_LIFETIME_SECONDS)
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        transaction.commit().await.map_err(storage_error)
    }

    /// Reports whether a session is current, removing it when it expired and recording its use.
    pub async fn use_browser_session(&self, digest: &TokenDigest, now: i64) -> Result<bool> {
        let session: Option<(i64, i64)> = sqlx::query_as(include_str!("../../queries/read_browser_session.sql"))
            .bind(digest.as_slice())
            .fetch_optional(self.pool())
            .await
            .map_err(storage_error)?;
        let Some((last_used_at, expires_at)) = session else {
            return Ok(false);
        };
        if expires_at <= now || last_used_at + SESSION_IDLE_SECONDS <= now {
            self.delete_browser_session(digest).await?;
            return Ok(false);
        }
        if now - last_used_at >= SESSION_TOUCH_SECONDS {
            sqlx::query(include_str!("../../queries/touch_browser_session.sql"))
                .bind(now)
                .bind(digest.as_slice())
                .execute(self.pool())
                .await
                .map_err(storage_error)?;
        }
        Ok(true)
    }

    pub async fn delete_browser_session(&self, digest: &TokenDigest) -> Result<()> {
        sqlx::query(include_str!("../../queries/delete_browser_session.sql"))
            .bind(digest.as_slice())
            .execute(self.pool())
            .await
            .map_err(storage_error)?;
        Ok(())
    }

    pub async fn preference(&self, name: &str) -> Result<Option<String>> {
        sqlx::query_scalar(include_str!("../../queries/read_preference.sql"))
            .bind(name)
            .fetch_optional(self.pool())
            .await
            .map_err(storage_error)
    }

    pub async fn set_preference(&self, name: &str, value: &str) -> Result<()> {
        sqlx::query(include_str!("../../queries/write_preference.sql"))
            .bind(name)
            .bind(value)
            .execute(self.pool())
            .await
            .map_err(storage_error)?;
        Ok(())
    }
}

fn storage_error(error: sqlx::Error) -> Error {
    Error::new("Browser login storage failed", error)
}
