use std::collections::BTreeSet;
use std::fs::File;
use std::io::Write;
use std::os::fd::OwnedFd;
use std::os::unix::fs::fchown;
use std::path::Path;

use rustix::fs::{AtFlags, CWD, Dir, FileType, Mode, OFlags, fchmod, fstat, fsync, openat, renameat, statat, unlinkat};
use rustix::io::Errno;

use crate::error::{Error, Result};
use crate::random::random_hex;

use super::token_file::{Owner, check_owner, read_token};

pub(super) const TOKEN: &str = "connector.token";
pub(super) const PENDING: &str = "connector.pending";
pub(super) const PREVIOUS: &str = "connector.previous";
const STAGING: &str = ".connector.preparing";
const TOKEN_BYTES: usize = 32;

pub(super) fn open_directory(path: &Path) -> Result<OwnedFd> {
    openat(
        CWD,
        path,
        OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::empty(),
    )
    .map_err(|_| io_failure())
}

pub(super) fn claim_directory(directory: &OwnedFd, owner: Owner) -> Result<()> {
    fchmod(directory, Mode::from_raw_mode(0o700)).map_err(|_| io_failure())?;
    fchown(directory, Some(owner.uid), Some(owner.gid)).map_err(|_| io_failure())?;
    fsync(directory).map_err(|_| io_failure())
}

pub(super) fn check_directory(directory: &OwnedFd, names: &mut BTreeSet<String>, owner: Owner) -> Result<()> {
    let metadata = fstat(directory).map_err(|_| io_failure())?;
    check_owner(metadata.st_uid, metadata.st_gid, metadata.st_mode, owner, 0o700)?;
    if names.remove(STAGING) {
        discard_staging(directory)?;
    }
    if names
        .iter()
        .any(|name| ![TOKEN, PENDING, PREVIOUS].contains(&name.as_str()))
    {
        return Err(Error::message("Connector directory contains unexpected files"));
    }
    for name in names.iter() {
        let file = openat(
            directory,
            name.as_str(),
            OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::NONBLOCK | OFlags::CLOEXEC,
            Mode::empty(),
        )
        .map_err(|_| io_failure())?;
        read_token(File::from(file), owner)?;
    }
    Ok(())
}

pub(super) fn write_pending(directory: &OwnedFd, owner: Owner) -> Result<()> {
    let written = write_staging(directory, owner).and_then(|()| replace(directory, STAGING, PENDING));
    match unlinkat(directory, STAGING, AtFlags::empty()) {
        Ok(()) => fsync(directory).map_err(|_| io_failure())?,
        Err(Errno::NOENT) => {}
        Err(_) => return Err(written.err().unwrap_or_else(io_failure)),
    }
    written
}

pub(super) fn replace(directory: &OwnedFd, source: &str, destination: &str) -> Result<()> {
    renameat(directory, source, directory, destination).map_err(|_| io_failure())?;
    fsync(directory).map_err(|_| io_failure())
}

pub(super) fn remove(directory: &OwnedFd, name: &str) -> Result<()> {
    unlinkat(directory, name, AtFlags::empty()).map_err(|_| io_failure())?;
    fsync(directory).map_err(|_| io_failure())
}

pub(super) fn list(directory: &OwnedFd) -> Result<BTreeSet<String>> {
    let mut names = BTreeSet::new();
    for entry in Dir::read_from(directory).map_err(|_| io_failure())? {
        let entry = entry.map_err(|_| io_failure())?;
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

fn write_staging(directory: &OwnedFd, owner: Owner) -> Result<()> {
    let descriptor = openat(
        directory,
        STAGING,
        OFlags::WRONLY | OFlags::CREATE | OFlags::EXCL | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::from_raw_mode(0o600),
    )
    .map_err(|_| io_failure())?;
    fchmod(&descriptor, Mode::from_raw_mode(0o600)).map_err(|_| io_failure())?;
    fchown(&descriptor, Some(owner.uid), Some(owner.gid)).map_err(|_| io_failure())?;
    let token = random_hex::<TOKEN_BYTES>().map_err(|_| io_failure())?;
    let mut file = File::from(descriptor);
    file.write_all(format!("{token}\n").as_bytes())
        .and_then(|()| file.sync_all())
        .map_err(|_| io_failure())
}

fn discard_staging(directory: &OwnedFd) -> Result<()> {
    let metadata = statat(directory, STAGING, AtFlags::SYMLINK_NOFOLLOW).map_err(|_| io_failure())?;
    if FileType::from_raw_mode(metadata.st_mode) != FileType::RegularFile || metadata.st_nlink != 1 {
        return Err(Error::message("Connector staging must be a regular file without links"));
    }
    remove(directory, STAGING)
}

fn io_failure() -> Error {
    Error::message("Cannot securely access or update connector token files")
}
