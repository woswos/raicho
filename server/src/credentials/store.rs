use sqlx::SqliteConnection;

use crate::error::{Error, Result};
use crate::persistence::Database;

use super::Credential;

#[derive(Debug, PartialEq, Eq)]
pub enum CredentialStatus {
    Unconfigured,
    Active,
    Revoked,
}

pub struct CredentialStore<'database> {
    database: &'database Database,
}

impl<'database> CredentialStore<'database> {
    pub fn new(database: &'database Database) -> Self {
        Self { database }
    }

    pub async fn status(&self) -> Result<CredentialStatus> {
        let mut connection = self
            .database
            .pool()
            .acquire()
            .await
            .map_err(storage_error)?;
        Ok(match read(&mut connection).await? {
            None => CredentialStatus::Unconfigured,
            Some((_, true)) => CredentialStatus::Revoked,
            Some((_, false)) => CredentialStatus::Active,
        })
    }

    pub async fn verify(&self, credential: &Credential) -> Result<bool> {
        let mut connection = self
            .database
            .pool()
            .acquire()
            .await
            .map_err(storage_error)?;
        Ok(match read(&mut connection).await? {
            Some((digest, false)) => credential.matches(&digest),
            _ => false,
        })
    }

    pub async fn initialize(&self, credential: &Credential) -> Result<()> {
        let mut transaction = self.database.pool().begin().await.map_err(storage_error)?;
        match read(&mut transaction).await? {
            None => {
                sqlx::query(include_str!(
                    "../../queries/initialize_connector_credential.sql"
                ))
                .bind(credential.digest.as_slice())
                .execute(&mut *transaction)
                .await
                .map_err(storage_error)?;
            }
            Some((digest, false)) if credential.matches(&digest) => {}
            _ => return Err(Error::message("Connector is already configured or revoked")),
        }
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn rotate(&self, current: &Credential, replacement: &Credential) -> Result<()> {
        if current.matches(&replacement.digest) {
            return Err(Error::message(
                "Replacement connector credential must differ",
            ));
        }
        let mut transaction = self.database.pool().begin().await.map_err(storage_error)?;
        match read(&mut transaction).await? {
            Some((digest, false)) if replacement.matches(&digest) => {}
            Some((digest, false)) if current.matches(&digest) => {
                sqlx::query(include_str!(
                    "../../queries/rotate_connector_credential.sql"
                ))
                .bind(replacement.digest.as_slice())
                .execute(&mut *transaction)
                .await
                .map_err(storage_error)?;
            }
            _ => return Err(Error::message("Current connector credential is not active")),
        }
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn revoke(&self) -> Result<()> {
        let mut transaction = self.database.pool().begin().await.map_err(storage_error)?;
        if read(&mut transaction).await?.is_none() {
            return Err(Error::message("Connector is not configured"));
        }
        sqlx::query(include_str!(
            "../../queries/revoke_connector_credential.sql"
        ))
        .execute(&mut *transaction)
        .await
        .map_err(storage_error)?;
        transaction.commit().await.map_err(storage_error)
    }

    pub async fn reactivate(&self, replacement: &Credential) -> Result<()> {
        let mut transaction = self.database.pool().begin().await.map_err(storage_error)?;
        match read(&mut transaction).await? {
            Some((digest, false)) if replacement.matches(&digest) => {}
            Some((digest, true)) if !replacement.matches(&digest) => {
                sqlx::query(include_str!(
                    "../../queries/reactivate_connector_credential.sql"
                ))
                .bind(replacement.digest.as_slice())
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

async fn read(connection: &mut SqliteConnection) -> Result<Option<(Vec<u8>, bool)>> {
    sqlx::query_as(include_str!("../../queries/read_connector_credential.sql"))
        .fetch_optional(connection)
        .await
        .map_err(storage_error)
}

fn storage_error(error: sqlx::Error) -> Error {
    Error::new("Cannot access connector credential state", error)
}
