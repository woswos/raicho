use std::fs::{DirBuilder, File, OpenOptions};
use std::os::unix::fs::{DirBuilderExt, OpenOptionsExt};
use std::path::Path;

use crate::error::{Error, Result};

pub(super) fn acquire(data_dir: &Path) -> Result<File> {
    DirBuilder::new()
        .recursive(true)
        .mode(0o700)
        .create(data_dir)
        .map_err(|error| Error::new("Cannot create application data directory", error))?;
    let lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .mode(0o600)
        .open(data_dir.join("instance.lock"))
        .map_err(|error| Error::new("Cannot open application instance lock", error))?;
    lock.try_lock().map_err(|error| {
        Error::new(
            "Application data directory is already in use or cannot be locked",
            error,
        )
    })?;
    Ok(lock)
}
