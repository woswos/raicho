use std::collections::BTreeSet;
use std::fmt;
use std::fs::File;
use std::io::Write;
use std::os::fd::OwnedFd;
use std::os::unix::fs::fchown;
use std::path::Path;
use std::str::FromStr;

use rustix::fs::{
    AtFlags, CWD, Dir, FileType, Mode, OFlags, fchmod, fstat, fsync, openat, renameat, statat,
    unlinkat,
};
use rustix::io::Errno;

use crate::error::{Error, Result};

use super::token_file::{Owner, check_owner, read_token};

const TOKEN: &str = "connector.token";
const PENDING: &str = "connector.pending";
const PREVIOUS: &str = "connector.previous";
const STAGING: &str = ".connector.preparing";
const TOKEN_BYTES: usize = 32;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TokenOperation {
    Init,
    Rotate,
    Reactivate,
    Publish,
    Finish,
    Check,
}

impl FromStr for TokenOperation {
    type Err = Error;

    fn from_str(value: &str) -> Result<Self> {
        Ok(match value {
            "init" => Self::Init,
            "rotate" => Self::Rotate,
            "reactivate" => Self::Reactivate,
            "publish" => Self::Publish,
            "finish" => Self::Finish,
            "check" => Self::Check,
            _ => return Err(Error::message("Unknown connector file operation")),
        })
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum TokenState {
    Pending,
    Current,
}

impl fmt::Display for TokenState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Pending => "pending",
            Self::Current => "current",
        })
    }
}

struct Present {
    token: bool,
    pending: bool,
    previous: bool,
}

pub fn operate_token_directory(
    operation: TokenOperation,
    path: &Path,
    owner: Owner,
) -> Result<TokenState> {
    let directory = openat(
        CWD,
        path,
        OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::empty(),
    )
    .map_err(io_error)?;
    let mut names = list(&directory)?;
    if names.is_empty() && matches!(operation, TokenOperation::Init | TokenOperation::Reactivate) {
        fchmod(&directory, Mode::from_raw_mode(0o700)).map_err(io_error)?;
        fchown(&directory, Some(owner.uid), Some(owner.gid)).map_err(|_| io_failure())?;
        fsync(&directory).map_err(io_error)?;
    }
    let metadata = fstat(&directory).map_err(io_error)?;
    check_owner(
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_mode,
        owner,
        0o700,
    )?;
    if names.remove(STAGING) {
        discard_staging(&directory)?;
    }
    if names
        .iter()
        .any(|name| ![TOKEN, PENDING, PREVIOUS].contains(&name.as_str()))
    {
        return Err(Error::message(
            "Connector directory contains unexpected files",
        ));
    }
    for name in &names {
        let file = openat(
            &directory,
            name.as_str(),
            OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::NONBLOCK | OFlags::CLOEXEC,
            Mode::empty(),
        )
        .map_err(io_error)?;
        read_token(File::from(file), owner)?;
    }
    let present = Present {
        token: names.contains(TOKEN),
        pending: names.contains(PENDING),
        previous: names.contains(PREVIOUS),
    };
    match operation {
        TokenOperation::Init | TokenOperation::Rotate | TokenOperation::Reactivate => {
            prepare_operation(operation, &directory, &present, owner)
        }
        TokenOperation::Publish | TokenOperation::Finish | TokenOperation::Check => {
            update_operation(operation, &directory, &present)
        }
    }
}

fn prepare_operation(
    operation: TokenOperation,
    directory: &OwnedFd,
    present: &Present,
    owner: Owner,
) -> Result<TokenState> {
    if operation == TokenOperation::Init {
        if present.previous || (present.token && present.pending) {
            return Err(Error::message("Initialization cannot recover a rotation"));
        }
        if present.token {
            return Ok(TokenState::Current);
        }
    } else if operation == TokenOperation::Reactivate
        && present.token
        && !present.pending
        && !present.previous
    {
        return Ok(TokenState::Current);
    } else if present.previous {
        if present.token && !present.pending {
            return Ok(TokenState::Current);
        }
        if present.pending && !present.token {
            replace(directory, PREVIOUS, TOKEN)?;
            return Ok(TokenState::Pending);
        }
        return Err(Error::message("Connector rotation files are inconsistent"));
    } else if !present.token && operation == TokenOperation::Rotate {
        return Err(Error::message(
            "Connector rotation requires the existing token",
        ));
    }
    if present.pending {
        return Ok(TokenState::Pending);
    }
    prepare(directory, owner)
}

fn update_operation(
    operation: TokenOperation,
    directory: &OwnedFd,
    present: &Present,
) -> Result<TokenState> {
    if operation == TokenOperation::Publish {
        if !present.pending || present.previous {
            return Err(Error::message(
                "Publishing requires a pending token without a backup",
            ));
        }
        if present.token {
            replace(directory, TOKEN, PREVIOUS)?;
        }
        replace(directory, PENDING, TOKEN)?;
    } else {
        if !present.token
            || present.pending
            || (operation == TokenOperation::Check && present.previous)
        {
            return Err(Error::message(
                "Connector token files need recovery before use",
            ));
        }
        if present.previous {
            unlinkat(directory, PREVIOUS, AtFlags::empty()).map_err(io_error)?;
            fsync(directory).map_err(io_error)?;
        }
    }
    Ok(TokenState::Current)
}

fn prepare(directory: &OwnedFd, owner: Owner) -> Result<TokenState> {
    let written = write_staging(directory, owner)
        .and_then(|()| replace(directory, STAGING, PENDING).map(|()| TokenState::Pending));
    match unlinkat(directory, STAGING, AtFlags::empty()) {
        Ok(()) => fsync(directory).map_err(io_error)?,
        Err(Errno::NOENT) => {}
        Err(error) => return Err(written.err().unwrap_or(io_error(error))),
    }
    written
}

fn write_staging(directory: &OwnedFd, owner: Owner) -> Result<()> {
    let descriptor = openat(
        directory,
        STAGING,
        OFlags::WRONLY | OFlags::CREATE | OFlags::EXCL | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::from_raw_mode(0o600),
    )
    .map_err(io_error)?;
    fchmod(&descriptor, Mode::from_raw_mode(0o600)).map_err(io_error)?;
    fchown(&descriptor, Some(owner.uid), Some(owner.gid)).map_err(|_| io_failure())?;
    let mut bytes = [0u8; TOKEN_BYTES];
    getrandom::fill(&mut bytes).map_err(|_| io_failure())?;
    let token: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();
    let mut file = File::from(descriptor);
    file.write_all(format!("{token}\n").as_bytes())
        .and_then(|()| file.sync_all())
        .map_err(|_| io_failure())
}

fn discard_staging(directory: &OwnedFd) -> Result<()> {
    let metadata = statat(directory, STAGING, AtFlags::SYMLINK_NOFOLLOW).map_err(io_error)?;
    if FileType::from_raw_mode(metadata.st_mode) != FileType::RegularFile || metadata.st_nlink != 1
    {
        return Err(Error::message(
            "Connector staging must be a regular file without links",
        ));
    }
    unlinkat(directory, STAGING, AtFlags::empty()).map_err(io_error)?;
    fsync(directory).map_err(io_error)
}

fn replace(directory: &OwnedFd, source: &str, destination: &str) -> Result<()> {
    renameat(directory, source, directory, destination).map_err(io_error)?;
    fsync(directory).map_err(io_error)
}

fn list(directory: &OwnedFd) -> Result<BTreeSet<String>> {
    let mut names = BTreeSet::new();
    for entry in Dir::read_from(directory).map_err(io_error)? {
        let entry = entry.map_err(io_error)?;
        let name = entry
            .file_name()
            .to_str()
            .map_err(|_| Error::message("Connector directory contains unexpected files"))?;
        if name != "." && name != ".." {
            names.insert(name.to_owned());
        }
    }
    Ok(names)
}

fn io_error(_: Errno) -> Error {
    io_failure()
}

fn io_failure() -> Error {
    Error::message("Cannot securely access or update connector token files")
}
