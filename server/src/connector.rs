mod authentication;
mod heartbeat;
mod listener;
mod route;
mod session;
mod state;
mod transport;
mod upgrade_stream;
mod wire;

use std::sync::{Arc, Mutex};

use axum::Router;
use raicho_protocol::limits_generated::MAXIMUM_PENDING_AUTHENTICATIONS;
use tokio::sync::{Semaphore, watch};

use crate::credentials::{CredentialStatus, CredentialStore};
use crate::persistence::Database;

pub use listener::ConnectorListener;
pub use state::BackendStatus;

const CONNECTION_LIMIT: usize = MAXIMUM_PENDING_AUTHENTICATIONS + 1;

pub struct Connector {
    database: Arc<Database>,
    state: Mutex<state::ConnectionState>,
    pending: Arc<Semaphore>,
    connections: Arc<Semaphore>,
    shutdown: watch::Sender<bool>,
}

impl Connector {
    pub fn new(database: Arc<Database>) -> Arc<Self> {
        Arc::new(Self {
            database,
            state: Mutex::new(state::ConnectionState::default()),
            pending: Arc::new(Semaphore::new(MAXIMUM_PENDING_AUTHENTICATIONS)),
            connections: Arc::new(Semaphore::new(CONNECTION_LIMIT)),
            shutdown: watch::channel(false).0,
        })
    }

    pub fn router(self: &Arc<Self>) -> Router {
        route::router(Arc::clone(self))
    }

    pub async fn snapshot(&self) -> BackendStatus {
        let credential_status = CredentialStore::new(&self.database).status().await;
        let state = self.state.lock().expect("Connector state lock poisoned");
        let status = match credential_status {
            Ok(CredentialStatus::Unconfigured) => "unconfigured",
            Ok(CredentialStatus::Revoked) => "revoked",
            Ok(CredentialStatus::Active) if state.active.is_some() => "connected",
            Ok(CredentialStatus::Active) => "disconnected",
            Err(_) => "unavailable",
        };
        BackendStatus {
            kind: "thunderbird",
            status,
            generation: state
                .active
                .as_ref()
                .map(|active| active.generation.clone()),
            last_error: if status == "unavailable" {
                Some("storage_unavailable")
            } else {
                state.last_error
            },
            heartbeat_count: state.heartbeat_count,
        }
    }

    pub async fn shutdown(&self) {
        {
            let mut state = self.state.lock().expect("Connector state lock poisoned");
            state.stopping = true;
            self.shutdown.send_replace(true);
        }
        let _all_sessions = Arc::clone(&self.connections)
            .acquire_many_owned(CONNECTION_LIMIT as u32)
            .await
            .expect("Connection semaphore remains open");
    }
}
