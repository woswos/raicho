use std::sync::LazyLock;

use sqlx::migrate::{Migration, MigrationType, Migrator};
use sqlx::{SqlSafeStr, SqlitePool};

use crate::error::{Error, Result};

// Applied migrations are checksummed, so each entry keeps its file's exact bytes.
macro_rules! migration {
    ($file:literal) => {
        ($file, include_str!(concat!("../../migrations/", $file)))
    };
}

const FILES: &[(&str, &str)] = &[migration!("0000_connector_credentials.sql")];

pub(super) static MIGRATIONS: LazyLock<Migrator> = LazyLock::new(|| {
    Migrator::with_migrations(
        FILES
            .iter()
            .map(|(file, sql)| {
                // sqlx derives the version and description from the file name the same way.
                let (version, description) = file
                    .trim_end_matches(".sql")
                    .split_once('_')
                    .expect("a migration file name starts with its version");
                Migration::new(
                    version.parse().expect("a migration version is an integer"),
                    description.replace('_', " ").into(),
                    MigrationType::Simple,
                    sql.into_sql_str(),
                    false,
                )
            })
            .collect(),
    )
});

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

#[cfg(test)]
mod tests {
    use std::fs;
    use std::path::Path;

    use super::{FILES, MIGRATIONS};

    #[test]
    fn every_migration_file_is_listed_under_its_file_name() {
        let directory = Path::new(env!("CARGO_MANIFEST_DIR")).join("migrations");
        let mut files: Vec<String> = fs::read_dir(directory)
            .unwrap()
            .map(|entry| entry.unwrap().file_name().into_string().unwrap())
            .filter(|name| name.ends_with(".sql"))
            .collect();
        files.sort();
        let listed: Vec<&str> = FILES.iter().map(|(file, _)| *file).collect();
        assert_eq!(listed, files);
    }

    #[test]
    fn versions_and_descriptions_come_from_the_file_names() {
        let parsed: Vec<(i64, &str)> = MIGRATIONS
            .iter()
            .map(|migration| (migration.version, &*migration.description))
            .collect();
        assert_eq!(parsed, [(0, "connector credentials")]);
    }

    #[test]
    fn applied_migrations_keep_their_recorded_checksums() {
        let checksums: Vec<String> = MIGRATIONS
            .iter()
            .map(|migration| migration.checksum.iter().map(|byte| format!("{byte:02X}")).collect())
            .collect();
        assert_eq!(
            checksums,
            ["398E200B80E67D0E112DE1E317F7F78F3B10E1111A322F217DEE93FD05863C8B3872FF682EE71DB19E1D0BC7B659B541"]
        );
    }
}
