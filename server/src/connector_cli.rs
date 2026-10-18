use std::env;
use std::ffi::OsString;
use std::path::PathBuf;

use raicho_server::credentials::{Credential, CredentialStatus, CredentialStore};
use raicho_server::error::{Error, Result};
use raicho_server::persistence::Database;

enum Operation {
    Initialize(PathBuf),
    Rotate {
        current: PathBuf,
        replacement: PathBuf,
    },
    Verify(PathBuf),
    Reactivate(PathBuf),
    Revoke,
    Status,
}

impl Operation {
    fn parse(arguments: &[OsString]) -> Result<Self> {
        match arguments {
            [command, operation] if command == "connector" && operation == "status" => {
                Ok(Self::Status)
            }
            [command, operation] if command == "connector" && operation == "revoke" => {
                Ok(Self::Revoke)
            }
            [command, operation, flag, path]
                if command == "connector" && flag == "--token-file" =>
            {
                match operation.to_str() {
                    Some("init") => Ok(Self::Initialize(path.into())),
                    Some("verify") => Ok(Self::Verify(path.into())),
                    Some("reactivate") => Ok(Self::Reactivate(path.into())),
                    _ => Err(usage()),
                }
            }
            [
                command,
                operation,
                replacement_flag,
                replacement,
                current_flag,
                current,
            ] if command == "connector"
                && operation == "rotate"
                && replacement_flag == "--token-file"
                && current_flag == "--current-token-file" =>
            {
                Ok(Self::Rotate {
                    current: current.into(),
                    replacement: replacement.into(),
                })
            }
            _ => Err(usage()),
        }
    }
}

pub async fn run(arguments: &[OsString]) -> Result<()> {
    let operation = Operation::parse(arguments)?;
    let directory = env::var_os("RAICHO_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| "/var/lib/raicho".into());
    if !directory.is_absolute() {
        return Err(Error::message("RAICHO_DATA_DIR must be an absolute path"));
    }
    let database = Database::open(&directory).await?;
    let result = execute(operation, &CredentialStore::new(&database)).await;
    database.close().await;
    if let Ok(status) = result {
        println!("connector: {status}");
    }
    result.map(|_| ())
}

async fn execute(operation: Operation, store: &CredentialStore<'_>) -> Result<&'static str> {
    match operation {
        Operation::Initialize(path) => {
            store.initialize(&Credential::read_file(&path)?).await?;
            Ok("initialized")
        }
        Operation::Rotate {
            current,
            replacement,
        } => {
            store
                .rotate(
                    &Credential::read_file(&current)?,
                    &Credential::read_file(&replacement)?,
                )
                .await?;
            Ok("rotated")
        }
        Operation::Verify(path) => {
            if !store.verify(&Credential::read_file(&path)?).await? {
                return Err(Error::message("Connector credential is not active"));
            }
            Ok("verified")
        }
        Operation::Revoke => {
            store.revoke().await?;
            Ok("revoked")
        }
        Operation::Reactivate(path) => {
            store.reactivate(&Credential::read_file(&path)?).await?;
            Ok("reactivated")
        }
        Operation::Status => Ok(match store.status().await? {
            CredentialStatus::Unconfigured => "unconfigured",
            CredentialStatus::Active => "active",
            CredentialStatus::Revoked => "revoked",
        }),
    }
}

fn usage() -> Error {
    Error::message(
        "Usage: connector init|verify|reactivate --token-file PATH; connector rotate --token-file NEW --current-token-file OLD; connector revoke|status",
    )
}
