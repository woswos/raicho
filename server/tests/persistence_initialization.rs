use std::fs;
use std::os::unix::fs::PermissionsExt;

use raicho_server::persistence::Database;
use sqlx::Connection;
use tempfile::tempdir;

#[tokio::test]
async fn fresh_database_has_connector_schema_and_survives_reopening() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    assert_eq!(database.version(), "3.51.3");
    let tables: Vec<String> =
        sqlx::query_scalar("SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT GLOB 'sqlite_*'")
            .fetch_all(database.pool())
            .await
            .unwrap();
    assert_eq!(tables, ["_sqlx_migrations", "connector_credentials"]);
    let versions: Vec<i64> = sqlx::query_scalar("SELECT version FROM _sqlx_migrations")
        .fetch_all(database.pool())
        .await
        .unwrap();
    assert_eq!(versions, [0]);
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    assert_eq!(reopened.version(), "3.51.3");
    let versions: Vec<i64> = sqlx::query_scalar("SELECT version FROM _sqlx_migrations")
        .fetch_all(reopened.pool())
        .await
        .unwrap();
    assert_eq!(versions, [0]);
    assert!(directory.path().join("raicho.sqlite3").is_file());
    reopened.close().await;
}

#[tokio::test]
async fn second_instance_is_rejected_until_the_first_releases_its_lock() {
    let directory = tempdir().unwrap();
    let first = Database::open(directory.path()).await.unwrap();
    assert!(Database::open(directory.path()).await.is_err());
    first.close().await;
    drop(first);
    let second = Database::open(directory.path()).await.unwrap();
    second.close().await;
}

#[tokio::test]
async fn corrupt_database_is_rejected_without_replacing_its_contents() {
    let directory = tempdir().unwrap();
    let path = directory.path().join("raicho.sqlite3");
    let contents = b"This is not a SQLite database.";
    fs::write(&path, contents).unwrap();
    assert!(Database::open(directory.path()).await.is_err());
    assert_eq!(fs::read(path).unwrap(), contents);
}

#[tokio::test]
async fn unrecognized_existing_schema_is_rejected_without_removing_tables() {
    let directory = tempdir().unwrap();
    let options = sqlx::sqlite::SqliteConnectOptions::new()
        .filename(directory.path().join("raicho.sqlite3"))
        .create_if_missing(true);
    let mut connection = sqlx::SqliteConnection::connect_with(&options).await.unwrap();
    sqlx::query("CREATE TABLE unrelated (value TEXT)")
        .execute(&mut connection)
        .await
        .unwrap();
    connection.close().await.unwrap();
    assert!(Database::open(directory.path()).await.is_err());
    let mut connection = sqlx::SqliteConnection::connect_with(&options).await.unwrap();
    let tables: Vec<String> = sqlx::query_scalar("SELECT name FROM sqlite_schema WHERE type='table'")
        .fetch_all(&mut connection)
        .await
        .unwrap();
    assert_eq!(tables, ["unrelated"]);
    connection.close().await.unwrap();
}

#[tokio::test]
async fn unwritable_database_is_rejected_without_replacing_it() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    database.close().await;
    drop(database);
    let path = directory.path().join("raicho.sqlite3");
    fs::set_permissions(&path, fs::Permissions::from_mode(0o400)).unwrap();
    assert!(Database::open(directory.path()).await.is_err());
    assert!(path.is_file());
    fs::set_permissions(path, fs::Permissions::from_mode(0o600)).unwrap();
}
