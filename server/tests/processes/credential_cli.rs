use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::process::{Command, Output};

use raicho_server::credentials::{Credential, SERVICE_OWNER};
use raicho_server::persistence::{CredentialStore, Database};
use tempfile::tempdir;

fn command(directory: &std::path::Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_raicho-server"))
        .env("RAICHO_DATA_DIR", directory)
        .env("RAICHO_WEB_DIR", "/does/not/exist")
        .args(arguments)
        .output()
        .unwrap()
}

#[test]
fn status_needs_no_web_assets_or_token_file() {
    let directory = tempdir().unwrap();
    let output = command(directory.path(), &["connector", "status"]);
    assert!(output.status.success(), "{:?}", output);
    assert_eq!(output.stdout, b"connector: unconfigured\n");
}

#[tokio::test]
async fn every_offline_operation_respects_the_running_instance_lock() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    for arguments in [
        vec!["connector", "status"],
        vec!["connector", "revoke"],
        vec!["connector", "init", "--token-file", "/unused"],
        vec!["connector", "verify", "--token-file", "/unused"],
        vec!["connector", "reactivate", "--token-file", "/unused"],
        vec![
            "connector",
            "rotate",
            "--token-file",
            "/unused",
            "--current-token-file",
            "/unused",
        ],
    ] {
        let output = command(directory.path(), &arguments);
        assert!(!output.status.success());
        assert!(String::from_utf8(output.stderr).unwrap().contains("already in use"));
    }
    database.close().await;
}

#[test]
fn missing_token_and_unknown_arguments_fail_without_echoing_arguments() {
    let directory = tempdir().unwrap();
    for arguments in [
        vec!["connector", "init", "--token-file", "/missing/secret"],
        vec!["connector", "init", "secret-should-not-be-echoed"],
        vec!["connector", "status", "secret-should-not-be-echoed"],
        vec!["unknown-secret-should-not-be-echoed"],
    ] {
        let output = command(directory.path(), &arguments);
        assert!(!output.status.success());
        let error = String::from_utf8(output.stderr).unwrap();
        assert!(!error.contains("secret-should-not-be-echoed"));
        assert!(error.starts_with("FAIL:"));
    }
}

#[tokio::test]
async fn status_and_revoke_report_the_stored_credential() {
    let directory = tempdir().unwrap();
    let database = Database::open(directory.path()).await.unwrap();
    CredentialStore::new(&database)
        .initialize(&Credential::parse(&"a".repeat(64)).unwrap())
        .await
        .unwrap();
    database.close().await;
    drop(database);
    for (arguments, expected) in [
        (["connector", "status"], "connector: active\n"),
        (["connector", "revoke"], "connector: revoked\n"),
        (["connector", "status"], "connector: revoked\n"),
    ] {
        let output = command(directory.path(), &arguments);
        assert!(output.status.success(), "{output:?}");
        assert_eq!(String::from_utf8(output.stdout).unwrap(), expected);
    }
}

#[test]
fn token_operations_require_files_owned_by_the_service() {
    let directory = tempdir().unwrap();
    let token = directory.path().join("connector.token");
    fs::write(&token, "a".repeat(64)).unwrap();
    fs::set_permissions(&token, fs::Permissions::from_mode(0o600)).unwrap();
    let metadata = fs::metadata(&token).unwrap();
    // Only root could give the fixture an owner other than the test's own.
    if (metadata.uid(), metadata.gid()) == (SERVICE_OWNER.uid, SERVICE_OWNER.gid) {
        return;
    }
    let token = token.to_str().unwrap();
    for arguments in [
        vec!["connector", "init", "--token-file", token],
        vec!["connector", "verify", "--token-file", token],
        vec!["connector", "reactivate", "--token-file", token],
        vec![
            "connector",
            "rotate",
            "--token-file",
            token,
            "--current-token-file",
            token,
        ],
        vec!["connector", "files", "check", directory.path().to_str().unwrap()],
    ] {
        let output = command(directory.path(), &arguments);
        assert!(!output.status.success(), "{arguments:?}");
        let error = String::from_utf8(output.stderr).unwrap();
        assert!(error.starts_with("FAIL:"), "{error}");
        assert!(!error.contains(&"a".repeat(64)));
    }
}
