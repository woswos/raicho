use raicho_protocol::authentication::ConnectorKeys;
use sqlx::SqliteExecutor;

use crate::credentials::Credential;
use crate::error::{Error, Result};

use super::Database;

#[derive(Debug, PartialEq, Eq)]
pub enum CredentialStatus {
    Unconfigured,
    Active,
    Revoked,
}

impl Database {
    pub async fn credential_status(&self) -> Result<CredentialStatus> {
        Ok(match read(self.pool()).await? {
            None => CredentialStatus::Unconfigured,
            Some((_, _, true)) => CredentialStatus::Revoked,
            Some((_, _, false)) => CredentialStatus::Active,
        })
    }

    pub async fn verify_credential(&self, credential: &Credential) -> Result<bool> {
        Ok(self
            .active_connector_keys()
            .await?
            .is_some_and(|keys| credential.matches(&keys.stored_key)))
    }

    pub async fn active_connector_keys(&self) -> Result<Option<ConnectorKeys>> {
        Ok(match read(self.pool()).await? {
            Some((stored_key, server_key, false)) => Some(ConnectorKeys {
                stored_key: stored_key.try_into().map_err(|_| invalid_key())?,
                server_key: server_key.try_into().map_err(|_| invalid_key())?,
            }),
            _ => None,
        })
    }

    pub async fn initialize_credential(&self, credential: &Credential) -> Result<()> {
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        match read(&mut *transaction).await? {
            None => {
                sqlx::query(include_str!("../../queries/initialize_connector_credential.sql"))
                    .bind(credential.stored_key())
                    .bind(credential.server_key())
                    .execute(&mut *transaction)
                    .await
                    .map_err(storage_error)?;
            }
            Some((stored_key, _, false)) if credential.matches(&stored_key) => {}
            _ => return Err(Error::message("Connector is already configured or revoked")),
        }
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn rotate_credential(&self, current: &Credential, replacement: &Credential) -> Result<()> {
        if current.matches(replacement.stored_key()) {
            return Err(Error::message("Replacement connector credential must differ"));
        }
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        match read(&mut *transaction).await? {
            Some((stored_key, _, false)) if replacement.matches(&stored_key) => {}
            Some((stored_key, _, false)) if current.matches(&stored_key) => {
                sqlx::query(include_str!("../../queries/rotate_connector_credential.sql"))
                    .bind(replacement.stored_key())
                    .bind(replacement.server_key())
                    .execute(&mut *transaction)
                    .await
                    .map_err(storage_error)?;
            }
            _ => return Err(Error::message("Current connector credential is not active")),
        }
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn revoke_credential(&self) -> Result<()> {
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        if read(&mut *transaction).await?.is_none() {
            return Err(Error::message("Connector is not configured"));
        }
        sqlx::query(include_str!("../../queries/revoke_connector_credential.sql"))
            .execute(&mut *transaction)
            .await
            .map_err(storage_error)?;
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn reactivate_credential(&self, replacement: &Credential) -> Result<()> {
        let mut transaction = self.pool().begin().await.map_err(storage_error)?;
        match read(&mut *transaction).await? {
            Some((stored_key, _, false)) if replacement.matches(&stored_key) => {}
            Some((stored_key, _, true)) if !replacement.matches(&stored_key) => {
                sqlx::query(include_str!("../../queries/reactivate_connector_credential.sql"))
                    .bind(replacement.stored_key())
                    .bind(replacement.server_key())
                    .execute(&mut *transaction)
                    .await
                    .map_err(storage_error)?;
            }
            _ => {
                return Err(Error::message(
                    "Connector reactivation requires a revoked backend and a new credential",
                ));
            }
        }
        transaction.commit().await.map_err(storage_error)
    }
}

async fn read(executor: impl SqliteExecutor<'_>) -> Result<Option<(Vec<u8>, Vec<u8>, bool)>> {
    sqlx::query_as(include_str!("../../queries/read_connector_credential.sql"))
        .fetch_optional(executor)
        .await
        .map_err(storage_error)
}

fn invalid_key() -> Error {
    Error::message("Stored connector credential keys are invalid")
}

fn storage_error(error: sqlx::Error) -> Error {
    Error::new("Cannot access connector credential state", error)
}
