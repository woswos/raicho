use std::time::Duration;

use serde_json::Value;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::time::Instant;

use crate::error::{Error, Result};

const MAXIMUM_RESPONSE_BYTES: u64 = 65536 + 4096;
const ATTEMPT_TIMEOUT: Duration = Duration::from_secs(5);
const RETRY_INTERVAL: Duration = Duration::from_secs(1);

enum Backend {
    Connected,
    Inactive,
    Waiting,
}

pub async fn wait_for_connector(address: &str, timeout: Duration) -> Result<()> {
    let deadline = Instant::now() + timeout;
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(Error::message(
                "Thunderbird did not establish an authenticated connection in time",
            ));
        }
        let status = tokio::time::timeout(remaining.min(ATTEMPT_TIMEOUT), status(address))
            .await
            .ok()
            .flatten();
        match status.as_ref().map_or(Backend::Waiting, backend) {
            Backend::Connected => return Ok(()),
            Backend::Inactive => {
                return Err(Error::message("Connector credential is not active"));
            }
            Backend::Waiting => {}
        }
        tokio::time::sleep(deadline.saturating_duration_since(Instant::now()).min(RETRY_INTERVAL)).await;
    }
}

// HTTP/1.0 keeps the reply unchunked and closes the connection after one response.
async fn status(address: &str) -> Option<Value> {
    let mut stream = TcpStream::connect(address).await.ok()?;
    stream
        .write_all(format!("GET /api/status HTTP/1.0\r\nHost: {address}\r\n\r\n").as_bytes())
        .await
        .ok()?;
    let mut response = Vec::new();
    stream
        .take(MAXIMUM_RESPONSE_BYTES)
        .read_to_end(&mut response)
        .await
        .ok()?;
    let separator = response.windows(4).position(|window| window == b"\r\n\r\n")?;
    let status_line = std::str::from_utf8(response.split(|byte| *byte == b'\r').next()?).ok()?;
    let mut parts = status_line.split(' ');
    if !parts.next()?.starts_with("HTTP/1.") || parts.next()? != "200" {
        return None;
    }
    serde_json::from_slice(&response[separator + 4..]).ok()
}

fn backend(payload: &Value) -> Backend {
    let backend = &payload["backend"];
    if backend["kind"] != "thunderbird" {
        return Backend::Waiting;
    }
    if matches!(backend["status"].as_str(), Some("revoked" | "unconfigured")) {
        return Backend::Inactive;
    }
    if payload["status"] == "ready"
        && backend["status"] == "connected"
        && backend["heartbeat_count"].as_u64().is_some_and(|count| count > 0)
    {
        Backend::Connected
    } else {
        Backend::Waiting
    }
}
