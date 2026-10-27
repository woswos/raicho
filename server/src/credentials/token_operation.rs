use std::fmt;
use std::str::FromStr;

use crate::error::{Error, Result};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TokenOperation {
    Initialize,
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
            "init" => Self::Initialize,
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
