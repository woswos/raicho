use raicho_server::persistence::Database;
use sqlx::SqlSafeStr;
use sqlx::migrate::{Migration, MigrationType, Migrator};
use tempfile::tempdir;

fn migrations(entries: &[(i64, &'static str)]) -> Migrator {
    Migrator::with_migrations(
        entries
            .iter()
            .map(|(version, statements)| {
                Migration::new(
                    *version,
                    "test migration".into(),
                    MigrationType::Simple,
                    (*statements).into_sql_str(),
                    false,
                )
            })
            .collect(),
    )
}

#[tokio::test]
async fn migration_persists_data_and_is_not_reapplied_on_restart() {
    let directory = tempdir().unwrap();
    let migration = migrations(&[(
        1,
        "CREATE TABLE settings (value TEXT); INSERT INTO settings VALUES ('retained')",
    )]);
    let database = Database::open_with_migrations(directory.path(), &migration)
        .await
        .unwrap();
    database.close().await;
    drop(database);
    let reopened = Database::open_with_migrations(directory.path(), &migration)
        .await
        .unwrap();
    let values: Vec<String> = sqlx::query_scalar("SELECT value FROM settings")
        .fetch_all(reopened.pool())
        .await
        .unwrap();
    assert_eq!(values, ["retained"]);
    reopened.close().await;
}

#[tokio::test]
async fn failed_migration_rolls_back_schema_and_history() {
    let directory = tempdir().unwrap();
    let migration = migrations(&[(1, "CREATE TABLE partial (value TEXT); INVALID SQL")]);
    assert!(
        Database::open_with_migrations(directory.path(), &migration)
            .await
            .is_err()
    );
    let database = Database::open_with_migrations(directory.path(), &migrations(&[]))
        .await
        .unwrap();
    let tables: Vec<String> = sqlx::query_scalar("SELECT name FROM sqlite_schema WHERE type='table'")
        .fetch_all(database.pool())
        .await
        .unwrap();
    assert_eq!(tables, ["_sqlx_migrations"]);
    let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM _sqlx_migrations")
        .fetch_one(database.pool())
        .await
        .unwrap();
    assert_eq!(count, 0);
    database.close().await;
}

#[tokio::test]
async fn checksum_drift_missing_and_future_versions_fail_closed() {
    let directory = tempdir().unwrap();
    // Versions above the production ones make production startup fail before it applies anything.
    let original = migrations(&[(100, "CREATE TABLE retained (value TEXT)")]);
    let database = Database::open_with_migrations(directory.path(), &original)
        .await
        .unwrap();
    database.close().await;
    drop(database);
    let changed = migrations(&[(100, "CREATE TABLE changed (value TEXT)")]);
    assert!(
        Database::open_with_migrations(directory.path(), &changed)
            .await
            .is_err()
    );
    assert!(Database::open(directory.path()).await.is_err());
    let missing = migrations(&[(101, "CREATE TABLE later (value TEXT)")]);
    assert!(
        Database::open_with_migrations(directory.path(), &missing)
            .await
            .is_err()
    );
    let unchanged = Database::open_with_migrations(directory.path(), &original)
        .await
        .unwrap();
    let tables: Vec<String> = sqlx::query_scalar("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")
        .fetch_all(unchanged.pool())
        .await
        .unwrap();
    assert_eq!(tables, ["_sqlx_migrations", "retained"]);
    unchanged.close().await;
}

#[tokio::test]
async fn dirty_migration_history_prevents_startup() {
    let directory = tempdir().unwrap();
    let migration = migrations(&[(1, "CREATE TABLE retained (value TEXT)")]);
    let database = Database::open_with_migrations(directory.path(), &migration)
        .await
        .unwrap();
    sqlx::query("UPDATE _sqlx_migrations SET success = false WHERE version = 1")
        .execute(database.pool())
        .await
        .unwrap();
    database.close().await;
    drop(database);
    assert!(
        Database::open_with_migrations(directory.path(), &migration)
            .await
            .is_err()
    );
}
