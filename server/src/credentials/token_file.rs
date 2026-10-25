use std::fs::OpenOptions;
use std::io::Read;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::Path;

use crate::error::{Error, Result};

use super::{Credential, TOKEN_HEX_LENGTH};

const SERVICE_UID: u32 = 10001;
const MAXIMUM_FILE_BYTES: u64 = TOKEN_HEX_LENGTH as u64 + 2;

impl Credential {
    pub fn read_file(path: &Path) -> Result<Self> {
        read_file(path, SERVICE_UID)
    }
}

fn read_file(path: &Path, expected_owner: u32) -> Result<Credential> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
        .map_err(|_| Error::message("Cannot open connector token file"))?;
    let metadata = file
        .metadata()
        .map_err(|_| Error::message("Cannot inspect connector token file"))?;
    if !metadata.is_file() || metadata.uid() != expected_owner || metadata.mode() & 0o7777 != 0o600
    {
        return Err(Error::message(
            "Connector token file must be regular, owned by UID 10001, and mode 0600",
        ));
    }
    let mut contents = Vec::new();
    file.take(MAXIMUM_FILE_BYTES)
        .read_to_end(&mut contents)
        .map_err(|_| Error::message("Cannot read connector token file"))?;
    if contents.last() == Some(&b'\n') {
        contents.pop();
    }
    let value = std::str::from_utf8(&contents)
        .map_err(|_| Error::message("Connector token must contain hexadecimal characters"))?;
    Credential::parse(value)
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};

    use tempfile::tempdir;

    use super::read_file;

    #[test]
    fn checks_permissions_owner_type_and_canonical_contents() {
        let directory = tempdir().unwrap();
        let path = directory.path().join("token");
        assert!(read_file(&path, super::SERVICE_UID).is_err());
        fs::write(&path, format!("{}\n", "a".repeat(64))).unwrap();
        let owner = fs::metadata(&path).unwrap().uid();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        assert!(read_file(&path, owner).is_ok());
        assert!(read_file(&path, owner + 1).is_err());
        for mode in [0o644, 0o640, 0o400, 0o660, 0o1600] {
            fs::set_permissions(&path, fs::Permissions::from_mode(mode)).unwrap();
            assert!(read_file(&path, owner).is_err());
        }
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        let link = directory.path().join("link");
        symlink(&path, &link).unwrap();
        assert!(read_file(&link, owner).is_err());
        assert!(read_file(directory.path(), owner).is_err());
        for contents in [
            format!("{}\n\n", "a".repeat(64)),
            "a".repeat(1024),
            format!(" {}", "a".repeat(64)),
        ] {
            fs::write(&path, contents).unwrap();
            assert!(read_file(&path, owner).is_err());
        }
    }
}
