use raicho_protocol::authentication::ConnectorKeys;
use raicho_server::credentials::Credential;
use raicho_server::persistence::{CredentialStatus, CredentialStore, Database};
use tempfile::tempdir;

fn credential(character: char) -> Credential {
    Credential::parse(&character.to_string().repeat(64)).unwrap()
}

#[tokio::test]
async fn initialization_is_idempotent_only_for_the_current_credential() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let store = CredentialStore::new(&database);
    let original = credential('a');
    assert_eq!(store.status().await.unwrap(), CredentialStatus::Unconfigured);
    assert!(!store.verify(&original).await.unwrap());
    store.initialize(&original).await.unwrap();
    store.initialize(&original).await.unwrap();
    assert!(store.initialize(&credential('b')).await.is_err());
    assert_eq!(store.status().await.unwrap(), CredentialStatus::Active);
    assert!(store.verify(&original).await.unwrap());
    database.close().await;
}

#[tokio::test]
async fn rotation_replaces_one_digest_and_can_resume_after_database_commit() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let store = CredentialStore::new(&database);
    let original = credential('a');
    let replacement = credential('b');
    store.initialize(&original).await.unwrap();
    assert!(store.rotate(&credential('c'), &replacement).await.is_err());
    assert!(store.verify(&original).await.unwrap());
    assert!(store.rotate(&original, &original).await.is_err());
    store.rotate(&original, &replacement).await.unwrap();
    assert!(!store.verify(&original).await.unwrap());
    assert!(store.verify(&replacement).await.unwrap());
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    let store = CredentialStore::new(&reopened);
    store.rotate(&original, &replacement).await.unwrap();
    assert!(!store.verify(&original).await.unwrap());
    assert!(store.verify(&replacement).await.unwrap());
    reopened.close().await;
}

#[tokio::test]
async fn revocation_survives_restart_and_cannot_be_undone_by_init_or_rotate() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    let store = CredentialStore::new(&database);
    store.initialize(&original).await.unwrap();
    store.revoke().await.unwrap();
    store.revoke().await.unwrap();
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    let store = CredentialStore::new(&reopened);
    assert_eq!(store.status().await.unwrap(), CredentialStatus::Revoked);
    assert!(!store.verify(&original).await.unwrap());
    assert!(store.initialize(&original).await.is_err());
    assert!(store.rotate(&original, &credential('b')).await.is_err());
    reopened.close().await;
}

#[tokio::test]
async fn explicit_reactivation_requires_a_new_credential_after_revocation() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    let replacement = credential('b');
    let store = CredentialStore::new(&database);
    assert!(store.reactivate(&replacement).await.is_err());
    store.initialize(&original).await.unwrap();
    assert!(store.reactivate(&replacement).await.is_err());
    store.revoke().await.unwrap();
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    let store = CredentialStore::new(&reopened);
    assert!(store.reactivate(&original).await.is_err());
    assert!(!store.verify(&original).await.unwrap());
    store.reactivate(&replacement).await.unwrap();
    store.reactivate(&replacement).await.unwrap();
    assert!(store.verify(&replacement).await.unwrap());
    assert!(!store.verify(&original).await.unwrap());
    assert!(store.reactivate(&original).await.is_err());
    reopened.close().await;
}

#[tokio::test]
async fn database_and_wal_never_contain_raw_credential() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let raw = "0123456789abcdef".repeat(4);
    let store = CredentialStore::new(&database);
    store.initialize(&Credential::parse(&raw).unwrap()).await.unwrap();
    for entry in std::fs::read_dir(directory.path()).unwrap() {
        let contents = std::fs::read(entry.unwrap().path()).unwrap();
        assert!(!contents.windows(raw.len()).any(|window| window == raw.as_bytes()));
    }
    let (backend, stored_key, server_key, revision): (String, Vec<u8>, Vec<u8>, i64) =
        sqlx::query_as("SELECT backend_kind, stored_key, server_key, revision FROM connector_credentials")
            .fetch_one(database.pool())
            .await
            .unwrap();
    let keys = ConnectorKeys::derive(&raw);
    assert_eq!(
        (backend.as_str(), stored_key, server_key, revision),
        ("thunderbird", keys.stored_key.to_vec(), keys.server_key.to_vec(), 1)
    );
    database.close().await;
}

#[tokio::test]
async fn existing_stage_one_database_migrates_without_enrolling_a_credential() {
    let directory = tempdir().unwrap();
    let empty = sqlx::migrate::Migrator::with_migrations(Vec::new());
    let old = Database::open_with_migrations(directory.path(), &empty).await.unwrap();
    old.close().await;
    drop(old);
    let database = Database::open(directory.path()).await.unwrap();
    assert_eq!(
        CredentialStore::new(&database).status().await.unwrap(),
        CredentialStatus::Unconfigured
    );
    database.close().await;
}
