use std::collections::HashMap;
use std::sync::Mutex;
use std::time::Duration;

use raicho_protocol::limits_generated::LIST_IDLE_TIMEOUT_MS;
use tokio::time::Instant;

use crate::persistence::TokenDigest;
use crate::random::random_hex;

pub const MAXIMUM_SESSION_CURSORS: usize = 4;
pub const MAXIMUM_CURSORS: usize = 16;
pub const CURSOR_IDLE: Duration = Duration::from_millis(LIST_IDLE_TIMEOUT_MS as u64);

struct Entry {
    session: TokenDigest,
    backend: String,
    issued: Instant,
}

/// Maps single-use browser cursors to backend cursors within one browser session.
#[derive(Default)]
pub struct Cursors {
    entries: Mutex<HashMap<String, Entry>>,
}

/// Backend cursors that the caller must close.
pub type Released = Vec<String>;

impl Cursors {
    pub fn issue(&self, session: &TokenDigest, backend: String) -> Option<(String, Released)> {
        let token = random_hex::<16>().ok()?;
        let mut entries = self.entries.lock().expect("Cursor lock poisoned");
        let mut released = expire(&mut entries);
        let session_count = entries.values().filter(|entry| entry.session == *session).count();
        if session_count >= MAXIMUM_SESSION_CURSORS {
            released.extend(evict_oldest(&mut entries, Some(session)));
        }
        if entries.len() >= MAXIMUM_CURSORS {
            released.extend(evict_oldest(&mut entries, None));
        }
        entries.insert(
            token.clone(),
            Entry {
                session: *session,
                backend,
                issued: Instant::now(),
            },
        );
        Some((token, released))
    }

    /// Removes and returns a cursor, which only the session that received it can use.
    pub fn take(&self, session: &TokenDigest, token: &str) -> (Option<String>, Released) {
        let mut entries = self.entries.lock().expect("Cursor lock poisoned");
        let released = expire(&mut entries);
        if entries.get(token).is_some_and(|entry| entry.session == *session) {
            return (entries.remove(token).map(|entry| entry.backend), released);
        }
        (None, released)
    }

    pub fn end_session(&self, session: &TokenDigest) -> Released {
        let mut entries = self.entries.lock().expect("Cursor lock poisoned");
        let tokens: Vec<String> = entries
            .iter()
            .filter(|(_, entry)| entry.session == *session)
            .map(|(token, _)| token.clone())
            .collect();
        tokens
            .iter()
            .filter_map(|token| entries.remove(token))
            .map(|entry| entry.backend)
            .collect()
    }
}

fn expire(entries: &mut HashMap<String, Entry>) -> Released {
    let now = Instant::now();
    let expired: Vec<String> = entries
        .iter()
        .filter(|(_, entry)| entry.issued + CURSOR_IDLE <= now)
        .map(|(token, _)| token.clone())
        .collect();
    expired
        .iter()
        .filter_map(|token| entries.remove(token))
        .map(|entry| entry.backend)
        .collect()
}

fn evict_oldest(entries: &mut HashMap<String, Entry>, session: Option<&TokenDigest>) -> Option<String> {
    let token = entries
        .iter()
        .filter(|(_, entry)| session.is_none_or(|session| entry.session == *session))
        .min_by_key(|(_, entry)| entry.issued)
        .map(|(token, _)| token.clone())?;
    entries.remove(&token).map(|entry| entry.backend)
}

#[cfg(test)]
mod tests {
    use super::{CURSOR_IDLE, Cursors, MAXIMUM_CURSORS, MAXIMUM_SESSION_CURSORS};

    #[tokio::test(start_paused = true)]
    async fn cursors_are_single_use_scoped_bounded_and_expire() {
        let cursors = Cursors::default();
        let (first, released) = cursors.issue(&[1; 32], "backend-1".into()).unwrap();
        assert!(released.is_empty());
        assert_eq!(cursors.take(&[2; 32], &first).0, None);
        assert_eq!(cursors.take(&[1; 32], &first).0.as_deref(), Some("backend-1"));
        assert_eq!(cursors.take(&[1; 32], &first).0, None);

        let mut released = Vec::new();
        for index in 0..=MAXIMUM_SESSION_CURSORS {
            tokio::time::advance(std::time::Duration::from_millis(1)).await;
            released.extend(cursors.issue(&[1; 32], format!("session-{index}")).unwrap().1);
        }
        assert_eq!(released, ["session-0"]);

        let mut released = Vec::new();
        for session in 2..(2 + MAXIMUM_CURSORS as u8) {
            tokio::time::advance(std::time::Duration::from_millis(1)).await;
            released.extend(cursors.issue(&[session; 32], format!("other-{session}")).unwrap().1);
        }
        assert_eq!(released.len(), MAXIMUM_SESSION_CURSORS);
        assert!(released.iter().all(|cursor| cursor.starts_with("session-")));

        tokio::time::advance(CURSOR_IDLE).await;
        let (token, released) = cursors.issue(&[9; 32], "fresh".into()).unwrap();
        assert_eq!(released.len(), MAXIMUM_CURSORS);
        assert_eq!(cursors.end_session(&[9; 32]), ["fresh"]);
        assert_eq!(cursors.take(&[9; 32], &token).0, None);
    }
}
