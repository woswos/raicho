use std::env;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};

use crate::error::{Error, Result};

const DEFAULT_BIND: &str = "0.0.0.0:8080";
const DEFAULT_CONNECTOR_BIND: &str = "0.0.0.0:8082";
const DEFAULT_DATA_DIR: &str = "/var/lib/raicho";
const DEFAULT_WEB_DIR: &str = "/usr/share/raicho/web";

pub struct Config {
    pub bind: SocketAddr,
    pub connector_bind: SocketAddr,
    pub data_dir: PathBuf,
    pub web_dir: PathBuf,
}

impl Config {
    pub fn from_environment() -> Result<Self> {
        let bind = text_variable("RAICHO_BIND", DEFAULT_BIND, "RAICHO_BIND must contain valid Unicode")?;
        let connector_bind = text_variable(
            "RAICHO_CONNECTOR_BIND",
            DEFAULT_CONNECTOR_BIND,
            "RAICHO_CONNECTOR_BIND must contain valid Unicode",
        )?;
        Self::parse(
            &bind,
            &connector_bind,
            &path_variable("RAICHO_DATA_DIR", DEFAULT_DATA_DIR),
            &path_variable("RAICHO_WEB_DIR", DEFAULT_WEB_DIR),
        )
    }

    pub fn data_dir_from_environment() -> Result<PathBuf> {
        absolute_data_dir(&path_variable("RAICHO_DATA_DIR", DEFAULT_DATA_DIR))
    }

    pub fn parse(bind: &str, connector_bind: &str, data_dir: &Path, web_dir: &Path) -> Result<Self> {
        let bind = bind
            .parse()
            .map_err(|error| Error::new("RAICHO_BIND must be an IP address and port", error))?;
        let connector_bind = connector_bind
            .parse()
            .map_err(|error| Error::new("RAICHO_CONNECTOR_BIND must be an IP address and port", error))?;
        if !web_dir.is_absolute() {
            return Err(Error::message("RAICHO_WEB_DIR must be an absolute path"));
        }
        Ok(Self {
            bind,
            connector_bind,
            data_dir: absolute_data_dir(data_dir)?,
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

fn text_variable(name: &str, default: &str, invalid: &'static str) -> Result<String> {
    match env::var(name) {
        Ok(value) => Ok(value),
        Err(env::VarError::NotPresent) => Ok(default.into()),
        Err(error) => Err(Error::new(invalid, error)),
    }
}

fn path_variable(name: &str, default: &str) -> PathBuf {
    env::var_os(name).map(PathBuf::from).unwrap_or_else(|| default.into())
}

fn absolute_data_dir(data_dir: &Path) -> Result<PathBuf> {
    if !data_dir.is_absolute() {
        return Err(Error::message("RAICHO_DATA_DIR must be an absolute path"));
    }
    Ok(data_dir.into())
}
