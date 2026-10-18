use std::process::{Command, Output};

use raicho_server::persistence::Database;
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
        assert!(
            String::from_utf8(output.stderr)
                .unwrap()
                .contains("already in use")
        );
    }
    database.close().await;
}

#[test]
fn missing_secret_and_unknown_arguments_fail_without_echoing_arguments() {
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
