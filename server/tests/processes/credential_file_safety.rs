use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};
use std::process::Command;

use raicho_server::credentials::{Owner, TokenState, operate_token_directory};
use rustix::fs::{CWD, FileType, Mode, mknodat};
use tempfile::TempDir;

struct Fixture {
    directory: TempDir,
    owner: Owner,
}

impl Fixture {
    fn new() -> Self {
        let directory = tempfile::tempdir().unwrap();
        fs::set_permissions(directory.path(), fs::Permissions::from_mode(0o700)).unwrap();
        let metadata = fs::metadata(directory.path()).unwrap();
        let fixture = Self {
            owner: Owner {
                uid: metadata.uid(),
                gid: metadata.gid(),
            },
            directory,
        };
        for operation in ["init", "publish", "finish"] {
            fixture.operate(fixture.directory.path(), operation).unwrap();
        }
        fixture
    }

    fn operate(&self, path: &Path, operation: &str) -> raicho_server::error::Result<TokenState> {
        operate_token_directory(operation.parse().unwrap(), path, self.owner)
    }

    fn rejects(&self, operation: &str) -> bool {
        self.operate(self.directory.path(), operation).is_err()
    }

    fn path(&self, name: &str) -> PathBuf {
        self.directory.path().join(format!("connector.{name}"))
    }
}

#[test]
fn insecure_files_directories_and_owners_fail_closed() {
    let fixture = Fixture::new();
    let original = fs::read(fixture.path("token")).unwrap();
    for mode in [0o640, 0o644, 0o400, 0o700] {
        fs::set_permissions(fixture.path("token"), fs::Permissions::from_mode(mode)).unwrap();
        assert!(fixture.rejects("rotate"), "{mode:o}");
    }
    fs::set_permissions(fixture.path("token"), fs::Permissions::from_mode(0o600)).unwrap();
    fs::set_permissions(fixture.directory.path(), fs::Permissions::from_mode(0o755)).unwrap();
    assert!(fixture.rejects("init"));
    fs::set_permissions(fixture.directory.path(), fs::Permissions::from_mode(0o700)).unwrap();
    let stranger = Owner {
        uid: fixture.owner.uid + 1,
        gid: fixture.owner.gid,
    };
    assert!(operate_token_directory("check".parse().unwrap(), fixture.directory.path(), stranger).is_err());
    assert_eq!(fs::read(fixture.path("token")).unwrap(), original);
    assert!(!fixture.path("pending").exists());
}

#[test]
fn links_nonregular_files_and_malformed_tokens_are_rejected() {
    let fixture = Fixture::new();
    let original = fs::read(fixture.path("token")).unwrap();
    fs::remove_file(fixture.path("token")).unwrap();
    symlink("/dev/null", fixture.path("token")).unwrap();
    assert!(fixture.rejects("check"));
    fs::remove_file(fixture.path("token")).unwrap();
    fs::create_dir(fixture.path("token")).unwrap();
    assert!(fixture.rejects("check"));
    fs::remove_dir(fixture.path("token")).unwrap();
    mknodat(
        CWD,
        fixture.path("token"),
        FileType::Fifo,
        Mode::from_raw_mode(0o600),
        0,
    )
    .unwrap();
    assert!(fixture.rejects("check"));
    fs::remove_file(fixture.path("token")).unwrap();
    let mut repeated = original.clone();
    repeated.push(b'\n');
    for contents in [Vec::new(), b"A".repeat(64), b"a".repeat(63), b"a".repeat(65), repeated] {
        fs::write(fixture.path("token"), &contents).unwrap();
        fs::set_permissions(fixture.path("token"), fs::Permissions::from_mode(0o600)).unwrap();
        assert!(fixture.rejects("check"), "{contents:?}");
    }
}

#[test]
fn directory_symlinks_and_hard_linked_tokens_are_rejected() {
    let fixture = Fixture::new();
    let original = fs::read(fixture.path("token")).unwrap();
    let link = fixture.directory.path().join("linked_directory");
    symlink(fixture.directory.path(), &link).unwrap();
    assert!(fixture.operate(&link, "check").is_err());
    fs::remove_file(&link).unwrap();
    fs::hard_link(fixture.path("token"), fixture.path("pending")).unwrap();
    assert!(fixture.rejects("rotate"));
    assert_eq!(fs::read(fixture.path("token")).unwrap(), original);
}

#[test]
fn unexpected_files_fail_and_the_command_never_prints_a_token() {
    let fixture = Fixture::new();
    let token = String::from_utf8(fs::read(fixture.path("token")).unwrap()).unwrap();
    fs::write(fixture.directory.path().join("unexpected"), b"").unwrap();
    assert!(fixture.rejects("init"));
    let output = Command::new(env!("CARGO_BIN_EXE_raicho-server"))
        .args(["connector", "files", "check"])
        .arg(fixture.directory.path())
        .output()
        .unwrap();
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).unwrap();
    assert!(stderr.starts_with("FAIL:"), "{stderr}");
    let printed = format!("{}{stderr}", String::from_utf8(output.stdout).unwrap());
    assert!(!printed.contains(token.trim()));
}
