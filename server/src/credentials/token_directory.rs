use std::collections::BTreeSet;
use std::os::fd::OwnedFd;
use std::path::Path;

use crate::error::{Error, Result};

use super::token_file::Owner;
use super::token_operation::{TokenOperation, TokenState};
use super::token_storage::{
    PENDING, PREVIOUS, TOKEN, check_directory, claim_directory, list, open_directory, remove, replace, write_pending,
};

pub fn operate_token_directory(operation: TokenOperation, path: &Path, owner: Owner) -> Result<TokenState> {
    let directory = open_directory(path)?;
    let mut names = list(&directory)?;
    if names.is_empty() && matches!(operation, TokenOperation::Initialize | TokenOperation::Reactivate) {
        claim_directory(&directory, owner)?;
    }
    check_directory(&directory, &mut names, owner)?;
    match operation {
        TokenOperation::Initialize | TokenOperation::Rotate | TokenOperation::Reactivate => {
            prepare_operation(operation, &directory, &names, owner)
        }
        TokenOperation::Publish | TokenOperation::Finish | TokenOperation::Check => {
            update_operation(operation, &directory, &names)
        }
    }
}

fn prepare_operation(
    operation: TokenOperation,
    directory: &OwnedFd,
    names: &BTreeSet<String>,
    owner: Owner,
) -> Result<TokenState> {
    let token = names.contains(TOKEN);
    let pending = names.contains(PENDING);
    let previous = names.contains(PREVIOUS);
    if operation == TokenOperation::Initialize {
        if previous || (token && pending) {
            return Err(Error::message("Initialization cannot recover a rotation"));
        }
        if token {
            return Ok(TokenState::Current);
        }
    } else if operation == TokenOperation::Reactivate && token && !pending && !previous {
        return Ok(TokenState::Current);
    } else if previous {
        if token && !pending {
            return Ok(TokenState::Current);
        }
        if pending && !token {
            replace(directory, PREVIOUS, TOKEN)?;
            return Ok(TokenState::Pending);
        }
        return Err(Error::message("Connector rotation files are inconsistent"));
    } else if !token && operation == TokenOperation::Rotate {
        return Err(Error::message("Connector rotation requires the existing token"));
    }
    if !pending {
        write_pending(directory, owner)?;
    }
    Ok(TokenState::Pending)
}

fn update_operation(operation: TokenOperation, directory: &OwnedFd, names: &BTreeSet<String>) -> Result<TokenState> {
    let token = names.contains(TOKEN);
    let pending = names.contains(PENDING);
    let previous = names.contains(PREVIOUS);
    if operation == TokenOperation::Publish {
        if !pending || previous {
            return Err(Error::message("Publishing requires a pending token without a backup"));
        }
        if token {
            replace(directory, TOKEN, PREVIOUS)?;
        }
        replace(directory, PENDING, TOKEN)?;
    } else {
        if !token || pending || (operation == TokenOperation::Check && previous) {
            return Err(Error::message("Connector token files need recovery before use"));
        }
        if previous {
            remove(directory, PREVIOUS)?;
        }
    }
    Ok(TokenState::Current)
}
