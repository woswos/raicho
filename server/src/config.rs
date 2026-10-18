use std::env;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};

use crate::error::{Error, Result};

pub struct Config {
    pub bind: SocketAddr,
    pub data_dir: PathBuf,
    pub web_dir: PathBuf,
}

impl Config {
    pub fn from_environment() -> Result<Self> {
        let bind = match env::var("RAICHO_BIND") {
            Ok(value) => value,
            Err(env::VarError::NotPresent) => "0.0.0.0:8080".into(),
            Err(error) => return Err(Error::new("RAICHO_BIND must contain valid Unicode", error)),
        };
        let data_dir = env::var_os("RAICHO_DATA_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| "/var/lib/raicho".into());
        let web_dir = env::var_os("RAICHO_WEB_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| "/usr/share/raicho/web".into());
        Self::parse(&bind, &data_dir, &web_dir)
    }

    pub fn parse(bind: &str, data_dir: &Path, web_dir: &Path) -> Result<Self> {
        let bind = bind
            .parse()
            .map_err(|error| Error::new("RAICHO_BIND must be an IP address and port", error))?;
        if !data_dir.is_absolute() {
            return Err(Error::message("RAICHO_DATA_DIR must be an absolute path"));
        }
        if !web_dir.is_absolute() {
            return Err(Error::message("RAICHO_WEB_DIR must be an absolute path"));
        }
        Ok(Self {
            bind,
            data_dir: data_dir.into(),
            web_dir: web_dir.into(),
        })
    }

    pub fn validate_web_assets(&self) -> Result<()> {
        if !self.web_dir.join("index.html").is_file() {
            return Err(Error::message("RAICHO_WEB_DIR must contain index.html"));
        }
        Ok(())
    }
}
