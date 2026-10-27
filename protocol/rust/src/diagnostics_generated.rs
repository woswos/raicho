#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BackendState {
    Unconfigured,
    Disconnected,
    Connected,
    Revoked,
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BackendError {
    AuthenticationFailed,
    AuthenticationTimeout,
    IncompatibleVersion,
    InvalidMessage,
    MessageTooLarge,
    UnexpectedMessage,
    StaleGeneration,
    HeartbeatTimeout,
    SessionReplaced,
    Disconnected,
    StorageUnavailable,
    ServerBusy,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ContractError {
    AuthenticationFailed,
    InvalidMessage,
    MessageTooLarge,
    IncompatibleVersion,
    UnexpectedMessage,
    StaleGeneration,
}

impl ContractError {
    pub const fn code(self) -> &'static str {
        match self {
            Self::AuthenticationFailed => "authentication_failed",
            Self::InvalidMessage => "invalid_message",
            Self::MessageTooLarge => "message_too_large",
            Self::IncompatibleVersion => "incompatible_version",
            Self::UnexpectedMessage => "unexpected_message",
            Self::StaleGeneration => "stale_generation",
        }
    }
}

impl std::fmt::Display for ContractError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for ContractError {}
