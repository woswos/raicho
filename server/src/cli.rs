use std::ffi::OsString;
use std::path::PathBuf;
use std::time::Duration;

use raicho_server::config::Config;
use raicho_server::credentials::{
    Credential, SERVICE_OWNER, TokenOperation, operate_token_directory, wait_for_connector,
};
use raicho_server::error::{Error, Result};
use raicho_server::persistence::{CredentialStatus, Database};

enum Operation {
    Credential(CredentialOperation),
    Files(TokenOperation, PathBuf),
    Wait,
}

enum CredentialOperation {
    Initialize(PathBuf),
    Rotate { current: PathBuf, replacement: PathBuf },
    Verify(PathBuf),
    Reactivate(PathBuf),
    Revoke,
    Status,
}

impl Operation {
    fn parse(arguments: &[OsString]) -> Result<Self> {
        match arguments {
            [command, operation] if command == "connector" && operation == "status" => {
                Ok(Self::Credential(CredentialOperation::Status))
            }
            [command, operation] if command == "connector" && operation == "revoke" => {
                Ok(Self::Credential(CredentialOperation::Revoke))
            }
            [command, operation] if command == "connector" && operation == "wait" => Ok(Self::Wait),
            [command, files, operation, directory] if command == "connector" && files == "files" => {
                let operation = operation.to_str().ok_or_else(usage)?.parse()?;
                Ok(Self::Files(operation, directory.into()))
            }
            [command, operation, flag, path] if command == "connector" && flag == "--token-file" => {
                let path = path.into();
                match operation.to_str() {
                    Some("init") => Ok(Self::Credential(CredentialOperation::Initialize(path))),
                    Some("verify") => Ok(Self::Credential(CredentialOperation::Verify(path))),
                    Some("reactivate") => Ok(Self::Credential(CredentialOperation::Reactivate(path))),
                    _ => Err(usage()),
                }
            }
            [command, operation, replacement_flag, replacement, current_flag, current]
                if command == "connector"
                    && operation == "rotate"
                    && replacement_flag == "--token-file"
                    && current_flag == "--current-token-file" =>
            {
                Ok(Self::Credential(CredentialOperation::Rotate {
                    current: current.into(),
                    replacement: replacement.into(),
                }))
            }
            _ => Err(usage()),
        }
    }
}

const STATUS_ADDRESS: &str = "raicho:8080";
const WAIT_TIMEOUT: Duration = Duration::from_secs(90);

pub async fn run(arguments: &[OsString]) -> Result<()> {
    let operation = match Operation::parse(arguments)? {
        Operation::Credential(operation) => operation,
        Operation::Files(operation, directory) => {
            println!("{}", operate_token_directory(operation, &directory, SERVICE_OWNER)?);
            return Ok(());
        }
        Operation::Wait => {
            wait_for_connector(STATUS_ADDRESS, WAIT_TIMEOUT).await?;
            println!("Authenticated Thunderbird connection and heartbeat verified");
            return Ok(());
        }
    };
    let database = Database::open(&Config::data_dir_from_environment()?).await?;
    let result = execute(operation, &database).await;
    database.close().await;
    if let Ok(status) = result {
        println!("connector: {status}");
    }
    result.map(|_| ())
}

async fn execute(operation: CredentialOperation, database: &Database) -> Result<&'static str> {
    match operation {
        CredentialOperation::Initialize(path) => {
            database.initialize_credential(&Credential::read_file(&path)?).await?;
            Ok("initialized")
        }
        CredentialOperation::Rotate { current, replacement } => {
            database
                .rotate_credential(&Credential::read_file(&current)?, &Credential::read_file(&replacement)?)
                .await?;
            Ok("rotated")
        }
        CredentialOperation::Verify(path) => {
            if !database.verify_credential(&Credential::read_file(&path)?).await? {
                return Err(Error::message("Connector credential is not active"));
            }
            Ok("verified")
        }
        CredentialOperation::Revoke => {
            database.revoke_credential().await?;
            Ok("revoked")
        }
        CredentialOperation::Reactivate(path) => {
            database.reactivate_credential(&Credential::read_file(&path)?).await?;
            Ok("reactivated")
        }
        CredentialOperation::Status => Ok(match database.credential_status().await? {
            CredentialStatus::Unconfigured => "unconfigured",
            CredentialStatus::Active => "active",
            CredentialStatus::Revoked => "revoked",
        }),
    }
}

fn usage() -> Error {
    Error::message(
        "Usage: connector init|verify|reactivate --token-file PATH; connector rotate --token-file NEW --current-token-file OLD; connector revoke|status|wait; connector files init|rotate|reactivate|publish|finish|check DIRECTORY",
    )
}
