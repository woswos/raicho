use sqlx::{SqlitePool, migrate::Migrator};

use crate::error::{Error, Result};

pub(super) async fn initialize(pool: &SqlitePool, migrations: &Migrator) -> Result<String> {
    let tables: Vec<String> = sqlx::query_scalar(include_str!("../../queries/list_application_tables.sql"))
        .fetch_all(pool)
        .await
        .map_err(|error| Error::new("Cannot inspect application database schema", error))?;
    if !tables.is_empty() && !tables.iter().any(|table| table == "_sqlx_migrations") {
        return Err(Error::message("Existing database has an unrecognized schema"));
    }
    migrations
        .run(pool)
        .await
        .map_err(|error| Error::new("Application database migration failed", error))?;
    // An unchanged migration history can succeed on SQLite's read-only fallback.
    sqlx::query(include_str!("../../queries/verify_database_writable.sql"))
        .execute(pool)
        .await
        .map_err(|error| Error::new("Application database is not writable", error))?;
    sqlx::query_scalar(include_str!("../../queries/read_sqlite_version.sql"))
        .fetch_one(pool)
        .await
        .map_err(|error| Error::new("Cannot read application database version", error))
}
