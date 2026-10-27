use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

use raicho_server::credentials::wait_for_connector;
use serde_json::json;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

fn status(backend: &str, heartbeats: u64, application: &str) -> String {
    let body = json!({
        "status": application,
        "backend": {"kind": "thunderbird", "status": backend, "heartbeat_count": heartbeats},
    })
    .to_string();
    format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{body}",
        body.len()
    )
}

async fn serve(responses: Vec<String>) -> (String, Arc<AtomicUsize>) {
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap().to_string();
    let requests = Arc::new(AtomicUsize::new(0));
    let counter = Arc::clone(&requests);
    tokio::spawn(async move {
        let mut responses = responses.into_iter().cycle();
        loop {
            let (mut stream, _) = listener.accept().await.unwrap();
            let mut request = Vec::new();
            let mut buffer = [0; 256];
            while !request.ends_with(b"\r\n\r\n") {
                let read = stream.read(&mut buffer).await.unwrap();
                if read == 0 {
                    break;
                }
                request.extend_from_slice(&buffer[..read]);
            }
            assert!(request.starts_with(b"GET /api/status HTTP/1.0\r\n"));
            counter.fetch_add(1, Ordering::SeqCst);
            let _ = stream.write_all(responses.next().unwrap().as_bytes()).await;
        }
    });
    (address, requests)
}

#[tokio::test]
async fn waits_for_an_authenticated_heartbeat_not_only_http_readiness() {
    let (address, requests) = serve(vec![
        status("disconnected", 0, "ready"),
        status("connected", 0, "ready"),
        status("connected", 1, "ready"),
    ])
    .await;
    wait_for_connector(&address, Duration::from_secs(10)).await.unwrap();
    assert_eq!(requests.load(Ordering::SeqCst), 3);
}

#[tokio::test]
async fn failures_are_bounded_and_never_echo_the_response() {
    let (address, requests) = serve(vec![
        "private malformed response".into(),
        "HTTP/1.1 503 Service Unavailable\r\n\r\nprivate".into(),
        "HTTP/1.1 200 OK\r\n\r\nprivate".into(),
        status("connected", 1, "unavailable"),
    ])
    .await;
    let error = wait_for_connector(&address, Duration::from_secs(3))
        .await
        .unwrap_err()
        .to_string();
    assert_eq!(
        error,
        "Thunderbird did not establish an authenticated connection in time"
    );
    assert!(requests.load(Ordering::SeqCst) >= 2);
}

#[tokio::test]
async fn revoked_or_unconfigured_credentials_fail_without_retrying() {
    for backend in ["revoked", "unconfigured"] {
        let (address, requests) = serve(vec![status(backend, 0, "ready")]).await;
        let error = wait_for_connector(&address, Duration::from_secs(10))
            .await
            .unwrap_err()
            .to_string();
        assert_eq!(error, "Connector credential is not active");
        assert_eq!(requests.load(Ordering::SeqCst), 1);
    }
}
