use raicho_protocol::authentication::ConnectorKeys;
use raicho_server::credentials::Credential;
use raicho_server::persistence::{CredentialStatus, Database};
use tempfile::tempdir;

fn credential(character: char) -> Credential {
    Credential::parse(&character.to_string().repeat(64)).unwrap()
}

#[tokio::test]
async fn initialization_is_idempotent_only_for_the_current_credential() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    assert_eq!(
        database.credential_status().await.unwrap(),
        CredentialStatus::Unconfigured
    );
    assert!(!database.verify_credential(&original).await.unwrap());
    database.initialize_credential(&original).await.unwrap();
    database.initialize_credential(&original).await.unwrap();
    assert!(database.initialize_credential(&credential('b')).await.is_err());
    assert_eq!(database.credential_status().await.unwrap(), CredentialStatus::Active);
    assert!(database.verify_credential(&original).await.unwrap());
    database.close().await;
}

#[tokio::test]
async fn rotation_replaces_one_digest_and_can_resume_after_database_commit() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    let replacement = credential('b');
    database.initialize_credential(&original).await.unwrap();
    assert!(
        database
            .rotate_credential(&credential('c'), &replacement)
            .await
            .is_err()
    );
    assert!(database.verify_credential(&original).await.unwrap());
    assert!(database.rotate_credential(&original, &original).await.is_err());
    database.rotate_credential(&original, &replacement).await.unwrap();
    assert!(!database.verify_credential(&original).await.unwrap());
    assert!(database.verify_credential(&replacement).await.unwrap());
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    reopened.rotate_credential(&original, &replacement).await.unwrap();
    assert!(!reopened.verify_credential(&original).await.unwrap());
    assert!(reopened.verify_credential(&replacement).await.unwrap());
    reopened.close().await;
}

#[tokio::test]
async fn revocation_survives_restart_and_cannot_be_undone_by_init_or_rotate() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    database.initialize_credential(&original).await.unwrap();
    database.revoke_credential().await.unwrap();
    database.revoke_credential().await.unwrap();
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    assert_eq!(reopened.credential_status().await.unwrap(), CredentialStatus::Revoked);
    assert!(!reopened.verify_credential(&original).await.unwrap());
    assert!(reopened.initialize_credential(&original).await.is_err());
    assert!(reopened.rotate_credential(&original, &credential('b')).await.is_err());
    reopened.close().await;
}

#[tokio::test]
async fn explicit_reactivation_requires_a_new_credential_after_revocation() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let original = credential('a');
    let replacement = credential('b');
    assert!(database.reactivate_credential(&replacement).await.is_err());
    database.initialize_credential(&original).await.unwrap();
    assert!(database.reactivate_credential(&replacement).await.is_err());
    database.revoke_credential().await.unwrap();
    database.close().await;
    drop(database);
    let reopened = Database::open(directory.path()).await.unwrap();
    assert!(reopened.reactivate_credential(&original).await.is_err());
    assert!(!reopened.verify_credential(&original).await.unwrap());
    reopened.reactivate_credential(&replacement).await.unwrap();
    reopened.reactivate_credential(&replacement).await.unwrap();
    assert!(reopened.verify_credential(&replacement).await.unwrap());
    assert!(!reopened.verify_credential(&original).await.unwrap());
    assert!(reopened.reactivate_credential(&original).await.is_err());
    reopened.close().await;
}

#[tokio::test]
async fn database_and_wal_never_contain_raw_credential() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    let raw = "0123456789abcdef".repeat(4);
    database
        .initialize_credential(&Credential::parse(&raw).unwrap())
        .await
        .unwrap();
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
        database.credential_status().await.unwrap(),
        CredentialStatus::Unconfigured
    );
    database.close().await;
}
