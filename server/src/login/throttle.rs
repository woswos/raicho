use std::collections::VecDeque;
use std::sync::Mutex;
use std::time::Duration;

use tokio::time::Instant;

pub const FAILURE_WINDOW: Duration = Duration::from_secs(60);
pub const MAXIMUM_FAILURES: usize = 5;

/// Limits failed logins for the deployment's one user, wherever they come from.
#[derive(Default)]
pub struct Throttle {
    failures: Mutex<VecDeque<Instant>>,
}

impl Throttle {
    /// Returns how long to wait before another attempt, if the limit is reached.
    pub fn wait(&self) -> Option<Duration> {
        let mut failures = self.failures.lock().expect("Login throttle lock poisoned");
        let now = Instant::now();
        while failures.front().is_some_and(|failure| *failure + FAILURE_WINDOW <= now) {
            failures.pop_front();
        }
        (failures.len() >= MAXIMUM_FAILURES).then(|| failures[0] + FAILURE_WINDOW - now)
    }

    pub fn fail(&self) {
        self.failures
            .lock()
            .expect("Login throttle lock poisoned")
            .push_back(Instant::now());
    }

    pub fn succeed(&self) {
        self.failures.lock().expect("Login throttle lock poisoned").clear();
    }
}

#[cfg(test)]
mod tests {
    use super::{FAILURE_WINDOW, MAXIMUM_FAILURES, Throttle};

    #[tokio::test(start_paused = true)]
    async fn failures_within_the_window_block_until_the_oldest_expires() {
        let throttle = Throttle::default();
        for _ in 0..MAXIMUM_FAILURES {
            assert_eq!(throttle.wait(), None);
            throttle.fail();
        }
        assert_eq!(throttle.wait(), Some(FAILURE_WINDOW));
        tokio::time::advance(FAILURE_WINDOW).await;
        assert_eq!(throttle.wait(), None);
        throttle.fail();
        throttle.succeed();
        assert_eq!(throttle.wait(), None);
    }
}
