mod authentication;
mod failure;
mod handshake;
mod heartbeat;
mod listener;
mod session;
mod state;
mod transport;
mod wire;

use std::sync::{Arc, Mutex};

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use raicho_protocol::limits_generated::{MAXIMUM_ACTIVE_CONNECTIONS, MAXIMUM_PENDING_AUTHENTICATIONS};
use tokio::sync::{Semaphore, watch};

use crate::persistence::{CredentialStatus, CredentialStore, Database};

pub use state::BackendStatus;

// Room beyond the pending and active sessions lets excess upgrades receive a 503.
pub const SOCKET_LIMIT: usize = MAXIMUM_ACTIVE_CONNECTIONS + 2 * MAXIMUM_PENDING_AUTHENTICATIONS;

pub struct Connector {
    database: Arc<Database>,
    state: Mutex<state::ConnectionState>,
    pending: Arc<Semaphore>,
    sockets: Arc<Semaphore>,
    shutdown: watch::Sender<bool>,
}

impl Connector {
    pub fn new(database: Arc<Database>) -> Arc<Self> {
        Arc::new(Self {
            database,
            state: Mutex::new(state::ConnectionState::default()),
            pending: Arc::new(Semaphore::new(MAXIMUM_PENDING_AUTHENTICATIONS)),
            sockets: Arc::new(Semaphore::new(SOCKET_LIMIT)),
            shutdown: watch::channel(false).0,
        })
    }

    pub async fn snapshot(&self) -> BackendStatus {
        let credential_status = CredentialStore::new(&self.database).status().await;
        let state = self.state.lock().expect("Connector state lock poisoned");
        let status = match credential_status {
            Ok(CredentialStatus::Unconfigured) => BackendState::Unconfigured,
            Ok(CredentialStatus::Revoked) => BackendState::Revoked,
            Ok(CredentialStatus::Active) if state.active.is_some() => BackendState::Connected,
            Ok(CredentialStatus::Active) => BackendState::Disconnected,
            Err(_) => BackendState::Unavailable,
        };
        BackendStatus {
            kind: "thunderbird",
            status,
            generation: state.active.as_ref().map(|active| active.generation.to_string()),
            last_error: if status == BackendState::Unavailable {
                Some(BackendError::StorageUnavailable)
            } else {
                state.last_error
            },
            heartbeat_count: state.heartbeat_count,
        }
    }

    pub async fn shutdown(&self) {
        {
            // Registrations check shutdown under this lock, so none can start after it.
            let _state = self.state.lock().expect("Connector state lock poisoned");
            self.shutdown.send_replace(true);
        }
        let _all_sockets = Arc::clone(&self.sockets)
            .acquire_many_owned(SOCKET_LIMIT as u32)
            .await
            .expect("Socket semaphore remains open");
    }
}
