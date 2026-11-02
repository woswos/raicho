use std::io::Write;
use std::path::Path;
use std::process::{Command, Output, Stdio};

use raicho_server::login;
use raicho_server::persistence::Database;
use tempfile::tempdir;

fn login_command(directory: &Path, operation: &str, input: &[u8]) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_raicho-server"))
        .env("RAICHO_DATA_DIR", directory)
        .env("RAICHO_WEB_DIR", "/does/not/exist")
        .args(["login", operation])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(input).unwrap();
    child.wait_with_output().unwrap()
}

fn stdout(output: &Output) -> String {
    String::from_utf8(output.stdout.clone()).unwrap()
}

#[tokio::test]
async fn login_commands_set_reset_and_revoke_from_standard_input() {
    let directory = tempdir().unwrap();
    assert_eq!(
        stdout(&login_command(directory.path(), "status", b"")),
        "login: unconfigured, 0 sessions\n"
    );
    let initialized = login_command(directory.path(), "init", b"first long password\n");
    assert!(initialized.status.success(), "{initialized:?}");
    assert_eq!(stdout(&initialized), "login: initialized\n");
    let repeated = login_command(directory.path(), "init", b"second long password\n");
    assert!(!repeated.status.success());
    assert!(String::from_utf8(repeated.stderr).unwrap().contains("use reset"));

    let database = Database::open(directory.path()).await.unwrap();
    let stored = database.login_password().await.unwrap().unwrap();
    assert!(!stored.contains("first long password"));
    database
        .create_browser_session(&login::digest(&"c".repeat(64)), login::now())
        .await
        .unwrap();
    database.close().await;
    drop(database);
    assert_eq!(
        stdout(&login_command(directory.path(), "status", b"")),
        "login: configured, 1 sessions\n"
    );

    let reset = login_command(directory.path(), "reset", b"second long password\r\n");
    assert_eq!(stdout(&reset), "login: reset, every browser session revoked\n");
    let database = Database::open(directory.path()).await.unwrap();
    assert_eq!(database.browser_session_count().await.unwrap(), 0);
    assert_ne!(database.login_password().await.unwrap().unwrap(), stored);
    database
        .create_browser_session(&login::digest(&"d".repeat(64)), login::now())
        .await
        .unwrap();
    database.close().await;
    drop(database);
    let revoked = login_command(directory.path(), "revoke", b"");
    assert_eq!(stdout(&revoked), "login: every browser session revoked\n");
    assert_eq!(
        stdout(&login_command(directory.path(), "status", b"")),
        "login: configured, 0 sessions\n"
    );
}

#[test]
fn short_long_and_unknown_inputs_fail_without_echoing_the_password() {
    let directory = tempdir().unwrap();
    for (operation, input) in [
        ("init", b"too short\n".to_vec()),
        ("init", vec![b'a'; 1100]),
        ("reset", b"".to_vec()),
        ("rotate", b"a long enough password\n".to_vec()),
    ] {
        let output = login_command(directory.path(), operation, &input);
        assert!(!output.status.success(), "{operation}");
        let errors = String::from_utf8(output.stderr).unwrap();
        assert!(
            !errors.contains("too short") && !errors.contains("long enough"),
            "{errors}"
        );
    }
    assert_eq!(
        stdout(&login_command(directory.path(), "status", b"")),
        "login: unconfigured, 0 sessions\n"
    );
}
