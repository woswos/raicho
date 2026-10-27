mod connector_credentials;
mod instance;
mod migrations;

use std::fs::File;
use std::path::Path;
use std::time::Duration;

use sqlx::sqlite::{SqliteConnectOptions, SqliteJournalMode, SqlitePoolOptions, SqliteSynchronous};
use sqlx::{ConnectOptions, SqlitePool, migrate::Migrator};

use crate::error::{Error, Result};

pub use connector_credentials::CredentialStatus;

pub struct Database {
    pool: SqlitePool,
    version: String,
    _instance: File,
}

impl Database {
    pub async fn open(data_dir: &Path) -> Result<Self> {
        Self::open_with_migrations(data_dir, &migrations::MIGRATIONS).await
    }

    pub async fn open_with_migrations(data_dir: &Path, migrations: &Migrator) -> Result<Self> {
        let instance = instance::acquire(data_dir)?;
        let options = SqliteConnectOptions::new()
            .filename(data_dir.join("raicho.sqlite3"))
            .create_if_missing(true)
            .foreign_keys(true)
            .journal_mode(SqliteJournalMode::Wal)
            .synchronous(SqliteSynchronous::Full)
            .busy_timeout(Duration::from_secs(5))
            .disable_statement_logging();
        let pool = SqlitePoolOptions::new()
            .min_connections(1)
            .max_connections(1)
            .acquire_timeout(Duration::from_secs(5))
            .connect_with(options)
            .await
            .map_err(|error| Error::new("Cannot open application database", error))?;
        let version = match migrations::initialize(&pool, migrations).await {
            Ok(version) => version,
            Err(error) => {
                pool.close().await;
                return Err(error);
            }
        };
        Ok(Self {
            pool,
            version,
            _instance: instance,
        })
    }

    pub fn pool(&self) -> &SqlitePool {
        &self.pool
    }

    pub fn version(&self) -> &str {
        &self.version
    }

    pub async fn check(&self) -> Result<()> {
        sqlx::query_scalar::<_, i64>(include_str!("../queries/count_migrations.sql"))
            .fetch_one(&self.pool)
            .await
            .map_err(|error| Error::new("Application database is unavailable", error))?;
        Ok(())
    }

    pub async fn close(&self) {
        self.pool.close().await;
    }
}
