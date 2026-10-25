use std::ffi::OsString;
use std::path::PathBuf;
use std::time::Duration;

use raicho_server::config::Config;
use raicho_server::connector_wait::wait_for_connector;
use raicho_server::credentials::{
    Credential, SERVICE_OWNER, TokenOperation, operate_token_directory,
};
use raicho_server::error::{Error, Result};
use raicho_server::persistence::{CredentialStatus, CredentialStore, Database};

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
    Files(TokenOperation, PathBuf),
    Wait,
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
            [command, operation] if command == "connector" && operation == "wait" => Ok(Self::Wait),
            [command, files, operation, directory]
                if command == "connector" && files == "files" =>
            {
                let operation = operation.to_str().ok_or_else(usage)?.parse()?;
                Ok(Self::Files(operation, directory.into()))
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

const STATUS_ADDRESS: &str = "raicho:8080";
const WAIT_TIMEOUT: Duration = Duration::from_secs(90);

pub async fn run(arguments: &[OsString]) -> Result<()> {
    let operation = Operation::parse(arguments)?;
    match operation {
        Operation::Files(operation, directory) => {
            println!(
                "{}",
                operate_token_directory(operation, &directory, SERVICE_OWNER)?
            );
            return Ok(());
        }
        Operation::Wait => {
            wait_for_connector(STATUS_ADDRESS, WAIT_TIMEOUT).await?;
            println!("Authenticated Thunderbird connection and heartbeat verified");
            return Ok(());
        }
        _ => {}
    }
    let database = Database::open(&Config::data_dir_from_environment()?).await?;
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
        Operation::Files(..) | Operation::Wait => unreachable!("handled without the database"),
    }
}

fn usage() -> Error {
    Error::message(
        "Usage: connector init|verify|reactivate --token-file PATH; connector rotate --token-file NEW --current-token-file OLD; connector revoke|status|wait; connector files init|rotate|reactivate|publish|finish|check DIRECTORY",
    )
}
