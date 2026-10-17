use std::time::{Duration, Instant};

use raicho_server::persistence::Database;
use sqlx::{Connection, SqlSafeStr, sqlite::SqliteConnectOptions};
use tempfile::tempdir;

#[tokio::test]
async fn connections_apply_durability_and_constraint_settings() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let journal: String = sqlx::query_scalar("PRAGMA journal_mode")
        .fetch_one(database.pool())
        .await
        .unwrap();
    let synchronous: i64 = sqlx::query_scalar("PRAGMA synchronous")
        .fetch_one(database.pool())
        .await
        .unwrap();
    let foreign_keys: i64 = sqlx::query_scalar("PRAGMA foreign_keys")
        .fetch_one(database.pool())
        .await
        .unwrap();
    let busy_timeout: i64 = sqlx::query_scalar("PRAGMA busy_timeout")
        .fetch_one(database.pool())
        .await
        .unwrap();
    assert_eq!(
        (journal.as_str(), synchronous, foreign_keys, busy_timeout),
        ("wal", 2, 1, 5000)
    );
    assert_eq!(database.pool().options().get_max_connections(), 1);
    database.close().await;
}

#[tokio::test]
async fn write_contention_times_out_without_losing_existing_state() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let options = SqliteConnectOptions::new().filename(directory.path().join("raicho.sqlite3"));
    let mut competing = sqlx::SqliteConnection::connect_with(&options)
        .await
        .unwrap();
    let transaction = competing
        .begin_with("BEGIN IMMEDIATE".into_sql_str())
        .await
        .unwrap();
    let started = Instant::now();
    let error = sqlx::query("CREATE TABLE contention (value TEXT)")
        .execute(database.pool())
        .await
        .unwrap_err();
    assert!(error.as_database_error().is_some());
    assert!(started.elapsed() >= Duration::from_secs(4));
    transaction.rollback().await.unwrap();
    competing.close().await.unwrap();
    database.check().await.unwrap();
    database.close().await;
}
