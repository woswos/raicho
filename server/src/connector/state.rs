use raicho_protocol::contract_generated::Generation;
use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use serde::Serialize;
use tokio::sync::watch;

use super::Connector;

#[derive(Clone, Debug, Serialize)]
pub struct BackendStatus {
    pub kind: &'static str,
    pub status: BackendState,
    pub generation: Option<String>,
    pub last_error: Option<BackendError>,
    pub heartbeat_count: u64,
}

#[derive(Default)]
pub(super) struct ConnectionState {
    pub active: Option<ActiveConnection>,
    pub last_error: Option<BackendError>,
    pub heartbeat_count: u64,
}

pub(super) struct ActiveConnection {
    pub generation: Generation,
    replacement: watch::Sender<bool>,
}

impl Connector {
    pub(super) fn register(&self, generation: Generation) -> Option<watch::Receiver<bool>> {
        let mut state = self.state.lock().expect("Connector state lock poisoned");
        if *self.shutdown.borrow() {
            return None;
        }
        let (replacement, receiver) = watch::channel(false);
        if let Some(previous) = state.active.replace(ActiveConnection {
            generation,
            replacement,
        }) {
            previous.replacement.send_replace(true);
        }
        state.last_error = None;
        state.heartbeat_count = 0;
        Some(receiver)
    }

    pub(super) fn reject(&self, reason: BackendError) {
        let mut state = self.state.lock().expect("Connector state lock poisoned");
        if state.active.is_none() && !*self.shutdown.borrow() {
            state.last_error = Some(reason);
        }
    }

    pub(super) fn heartbeat(&self, generation: &Generation) -> bool {
        let mut state = self.state.lock().expect("Connector state lock poisoned");
        if state
            .active
            .as_ref()
            .is_some_and(|active| active.generation == *generation)
        {
            state.heartbeat_count = state.heartbeat_count.saturating_add(1);
            true
        } else {
            false
        }
    }

    pub(super) fn disconnect(&self, generation: &Generation, reason: BackendError) {
        let mut state = self.state.lock().expect("Connector state lock poisoned");
        if state
            .active
            .as_ref()
            .is_some_and(|active| active.generation == *generation)
        {
            state.active = None;
            state.last_error = Some(reason);
        }
    }
}
