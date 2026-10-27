use raicho_protocol::ContractError;
use raicho_protocol::contract_generated::ProtocolErrorCode;
use raicho_protocol::diagnostics_generated::BackendError;
use raicho_protocol::limits_generated::{
    AUTHENTICATION_FAILURE_CLOSE_CODE, PROTOCOL_FAILURE_CLOSE_CODE, SESSION_REPLACED_CLOSE_CODE,
};

const TRY_AGAIN_LATER_CLOSE_CODE: usize = 1013;

#[derive(Clone, Copy)]
pub(super) struct Failure {
    pub diagnostic: BackendError,
}

impl Failure {
    pub fn new(diagnostic: BackendError) -> Self {
        Self { diagnostic }
    }

    pub fn code(self) -> ProtocolErrorCode {
        match self.diagnostic {
            BackendError::AuthenticationFailed | BackendError::AuthenticationTimeout => {
                ProtocolErrorCode::AuthenticationFailed
            }
            BackendError::IncompatibleVersion => ProtocolErrorCode::IncompatibleVersion,
            BackendError::InvalidMessage => ProtocolErrorCode::InvalidMessage,
            BackendError::MessageTooLarge => ProtocolErrorCode::MessageTooLarge,
            BackendError::UnexpectedMessage => ProtocolErrorCode::UnexpectedMessage,
            BackendError::StaleGeneration => ProtocolErrorCode::StaleGeneration,
            BackendError::HeartbeatTimeout => ProtocolErrorCode::HeartbeatTimeout,
            BackendError::SessionReplaced => ProtocolErrorCode::SessionReplaced,
            BackendError::Disconnected | BackendError::StorageUnavailable | BackendError::ServerBusy => {
                ProtocolErrorCode::ServerBusy
            }
        }
    }

    pub fn close_code(self) -> u16 {
        let code = match self.code() {
            ProtocolErrorCode::AuthenticationFailed => AUTHENTICATION_FAILURE_CLOSE_CODE,
            ProtocolErrorCode::SessionReplaced => SESSION_REPLACED_CLOSE_CODE,
            ProtocolErrorCode::HeartbeatTimeout | ProtocolErrorCode::ServerBusy => TRY_AGAIN_LATER_CLOSE_CODE,
            _ => PROTOCOL_FAILURE_CLOSE_CODE,
        };
        code as u16
    }
}

impl From<ContractError> for Failure {
    fn from(error: ContractError) -> Self {
        Self::new(match error {
            ContractError::AuthenticationFailed => BackendError::AuthenticationFailed,
            ContractError::InvalidMessage => BackendError::InvalidMessage,
            ContractError::MessageTooLarge => BackendError::MessageTooLarge,
            ContractError::IncompatibleVersion => BackendError::IncompatibleVersion,
            ContractError::UnexpectedMessage => BackendError::UnexpectedMessage,
            ContractError::StaleGeneration => BackendError::StaleGeneration,
        })
    }
}
