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
