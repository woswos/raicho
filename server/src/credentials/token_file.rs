use std::fs::File;
use std::io::Read;
use std::os::unix::fs::MetadataExt;
use std::path::Path;

use rustix::fs::{Mode, OFlags, open};

use crate::error::{Error, Result};

use super::{Credential, TOKEN_HEX_LENGTH, is_canonical_token};

const MAXIMUM_FILE_BYTES: u64 = TOKEN_HEX_LENGTH as u64 + 2;

#[derive(Clone, Copy)]
pub struct Owner {
    pub uid: u32,
    pub gid: u32,
}

pub const SERVICE_OWNER: Owner = Owner { uid: 10001, gid: 10001 };

impl Credential {
    pub fn read_file(path: &Path) -> Result<Self> {
        Credential::parse(&read_file(path, SERVICE_OWNER)?)
    }
}

fn read_file(path: &Path, owner: Owner) -> Result<String> {
    let flags = OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::NONBLOCK | OFlags::CLOEXEC;
    let descriptor =
        open(path, flags, Mode::empty()).map_err(|_| Error::message("Cannot open connector token file"))?;
    read_token(File::from(descriptor), owner)
}

pub(super) fn check_owner(uid: u32, gid: u32, mode: u32, owner: Owner, expected: u32) -> Result<()> {
    if uid != owner.uid || gid != owner.gid || mode & 0o7777 != expected {
        return Err(Error::message(
            "Connector files require the configured owner and private modes",
        ));
    }
    Ok(())
}

pub(super) fn read_token(file: File, owner: Owner) -> Result<String> {
    let metadata = file
        .metadata()
        .map_err(|_| Error::message("Cannot inspect connector token file"))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(Error::message("Connector tokens must be regular files without links"));
    }
    check_owner(metadata.uid(), metadata.gid(), metadata.mode(), owner, 0o600)?;
    let mut contents = Vec::new();
    file.take(MAXIMUM_FILE_BYTES)
        .read_to_end(&mut contents)
        .map_err(|_| Error::message("Cannot read connector token file"))?;
    if contents.last() == Some(&b'\n') {
        contents.pop();
    }
    match String::from_utf8(contents) {
        Ok(token) if is_canonical_token(&token) => Ok(token),
        _ => Err(Error::message("Connector token has an invalid format")),
    }
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};

    use tempfile::tempdir;

    use super::{Owner, read_file};

    #[test]
    fn checks_permissions_owner_links_type_and_canonical_contents() {
        let directory = tempdir().unwrap();
        let path = directory.path().join("token");
        assert!(read_file(&path, Owner { uid: 0, gid: 0 }).is_err());
        fs::write(&path, format!("{}\n", "a".repeat(64))).unwrap();
        let metadata = fs::metadata(&path).unwrap();
        let owner = Owner {
            uid: metadata.uid(),
            gid: metadata.gid(),
        };
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        assert!(read_file(&path, owner).is_ok());
        assert!(
            read_file(
                &path,
                Owner {
                    uid: owner.uid + 1,
                    ..owner
                }
            )
            .is_err()
        );
        assert!(
            read_file(
                &path,
                Owner {
                    gid: owner.gid + 1,
                    ..owner
                }
            )
            .is_err()
        );
        for mode in [0o644, 0o640, 0o400, 0o660, 0o1600] {
            fs::set_permissions(&path, fs::Permissions::from_mode(mode)).unwrap();
            assert!(read_file(&path, owner).is_err());
        }
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        let link = directory.path().join("link");
        fs::hard_link(&path, &link).unwrap();
        assert!(read_file(&path, owner).is_err());
        fs::remove_file(&link).unwrap();
        symlink(&path, &link).unwrap();
        assert!(read_file(&link, owner).is_err());
        assert!(read_file(directory.path(), owner).is_err());
        for contents in [
            format!("{}\n\n", "a".repeat(64)),
            "a".repeat(1024),
            format!(" {}", "a".repeat(64)),
            "A".repeat(64),
        ] {
            fs::write(&path, contents).unwrap();
            assert!(read_file(&path, owner).is_err());
        }
    }
}
