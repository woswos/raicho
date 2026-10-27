use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::{Path, PathBuf};

use raicho_server::credentials::{Owner, TokenOperation, TokenState, operate_token_directory};
use tempfile::TempDir;

struct Fixture {
    directory: TempDir,
    owner: Owner,
}

impl Fixture {
    fn new() -> Self {
        let directory = tempfile::tempdir().unwrap();
        let metadata = fs::metadata(directory.path()).unwrap();
        fs::set_permissions(directory.path(), fs::Permissions::from_mode(0o700)).unwrap();
        Self {
            owner: Owner {
                uid: metadata.uid(),
                gid: metadata.gid(),
            },
            directory,
        }
    }

    fn operate(&self, operation: &str) -> raicho_server::error::Result<TokenState> {
        operate_token_directory(
            operation.parse().unwrap(),
            self.directory.path(),
            self.owner,
        )
    }

    fn state(&self, operation: &str) -> TokenState {
        self.operate(operation).unwrap()
    }

    fn path(&self, name: &str) -> PathBuf {
        self.directory.path().join(format!("connector.{name}"))
    }

    fn contents(&self, name: &str) -> Vec<u8> {
        fs::read(self.path(name)).unwrap()
    }

    fn write_token(&self, name: &str, character: char) {
        fs::write(self.path(name), character.to_string().repeat(64)).unwrap();
        fs::set_permissions(self.path(name), fs::Permissions::from_mode(0o600)).unwrap();
    }

    fn initialized(&self) -> Vec<u8> {
        assert_eq!(self.state("init"), TokenState::Pending);
        self.state("publish");
        self.state("finish");
        self.contents("token")
    }

    fn mode(&self, path: &Path) -> u32 {
        fs::metadata(path).unwrap().mode() & 0o7777
    }
}

#[test]
fn initialization_is_private_and_idempotent() {
    let fixture = Fixture::new();
    fs::set_permissions(fixture.directory.path(), fs::Permissions::from_mode(0o755)).unwrap();
    assert_eq!(fixture.state("init"), TokenState::Pending);
    let token = fixture.contents("pending");
    assert_eq!(token.len(), 65);
    assert!(
        token[..64]
            .iter()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    );
    assert_eq!(token[64], b'\n');
    assert_eq!(fixture.mode(&fixture.path("pending")), 0o600);
    assert_eq!(fixture.mode(fixture.directory.path()), 0o700);
    assert_eq!(fixture.state("init"), TokenState::Pending);
    assert_eq!(fixture.contents("pending"), token);
    fixture.state("publish");
    fixture.state("finish");
    assert_eq!(fixture.state("init"), TokenState::Current);
    assert_eq!(fixture.state("check"), TokenState::Current);
    assert_eq!(fixture.contents("token"), token);
}

#[test]
fn rotation_preserves_the_committed_file_until_finish() {
    let fixture = Fixture::new();
    let original = fixture.initialized();
    assert_eq!(fixture.state("rotate"), TokenState::Pending);
    let replacement = fixture.contents("pending");
    assert_ne!(original, replacement);
    assert_eq!(fixture.state("rotate"), TokenState::Pending);
    assert_eq!(fixture.contents("pending"), replacement);
    fixture.state("publish");
    assert_eq!(fixture.contents("previous"), original);
    assert_eq!(fixture.contents("token"), replacement);
    assert_eq!(fixture.state("rotate"), TokenState::Current);
    assert!(fixture.operate("check").is_err());
    fixture.state("finish");
    assert!(!fixture.path("previous").exists());
    assert_eq!(fixture.state("check"), TokenState::Current);
}

#[test]
fn reactivation_resumes_a_prepared_or_published_replacement() {
    let fixture = Fixture::new();
    fixture.initialized();
    fixture.state("rotate");
    assert_eq!(fixture.state("reactivate"), TokenState::Pending);
    let replacement = fixture.contents("pending");
    assert_eq!(fixture.state("reactivate"), TokenState::Pending);
    assert_eq!(fixture.contents("pending"), replacement);
    fixture.state("publish");
    assert_eq!(fixture.state("reactivate"), TokenState::Current);
    fixture.state("finish");
    assert_eq!(fixture.state("reactivate"), TokenState::Current);
    assert_eq!(fixture.contents("token"), replacement);
}

#[test]
fn reactivation_handles_missing_local_token_files() {
    let fixture = Fixture::new();
    fs::set_permissions(fixture.directory.path(), fs::Permissions::from_mode(0o755)).unwrap();
    assert_eq!(fixture.state("reactivate"), TokenState::Pending);
    let replacement = fixture.contents("pending");
    assert_eq!(fixture.state("reactivate"), TokenState::Pending);
    assert_eq!(fixture.contents("pending"), replacement);
    fixture.state("publish");
    fixture.state("finish");
    assert_eq!(fixture.state("check"), TokenState::Current);
}

#[test]
fn interrupted_publication_resumes_without_another_token() {
    let fixture = Fixture::new();
    fixture.write_token("previous", 'a');
    fixture.write_token("pending", 'b');
    assert_eq!(fixture.state("rotate"), TokenState::Pending);
    assert_eq!(fixture.contents("token"), b"a".repeat(64));
    assert_eq!(fixture.contents("pending"), b"b".repeat(64));
    fixture.state("publish");
    fixture.state("finish");
    assert_eq!(fixture.contents("token"), b"b".repeat(64));
}

#[test]
fn missing_and_inconsistent_states_fail_without_mutation() {
    let fixture = Fixture::new();
    for operation in ["rotate", "publish", "finish", "check"] {
        assert!(fixture.operate(operation).is_err(), "{operation}");
    }
    fixture.initialized();
    fixture.write_token("previous", 'b');
    assert!(fixture.operate("init").is_err());
    fixture.write_token("pending", 'c');
    for operation in ["rotate", "publish", "finish", "check"] {
        assert!(fixture.operate(operation).is_err(), "{operation}");
    }
    assert_eq!(fixture.contents("previous"), b"b".repeat(64));
    assert_eq!(fixture.contents("pending"), b"c".repeat(64));
}

#[test]
fn a_killed_preparation_leaves_a_recoverable_directory() {
    let fixture = Fixture::new();
    let original = fixture.initialized();
    let staging = fixture.directory.path().join(".connector.preparing");
    fs::write(&staging, b"partial").unwrap();
    assert_eq!(fixture.state("rotate"), TokenState::Pending);
    assert!(!staging.exists());
    assert_eq!(fixture.contents("token"), original);
    fs::remove_file(fixture.path("pending")).unwrap();
    std::os::unix::fs::symlink(fixture.path("token"), &staging).unwrap();
    assert!(fixture.operate("check").is_err());
    assert!(staging.is_symlink());
}

#[test]
fn unknown_operations_are_rejected() {
    assert!("delete".parse::<TokenOperation>().is_err());
}
