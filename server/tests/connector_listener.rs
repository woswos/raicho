mod support;

use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::client::IntoClientRequest;

use support::{Fixture, ORIGIN};

#[tokio::test]
async fn partial_upgrade_headers_have_an_absolute_deadline() {
    let fixture = Fixture::new().await;
    let mut stream = TcpStream::connect(address(&fixture)).await.unwrap();
    stream
        .write_all(b"GET /connector/v1 HTTP/1.1\r\n")
        .await
        .unwrap();
    tokio::time::sleep(Duration::from_millis(20)).await;
    tokio::time::pause();
    tokio::time::advance(Duration::from_secs(5)).await;
    tokio::time::resume();
    let mut response = [0; 128];
    let result = tokio::time::timeout(Duration::from_secs(2), stream.read(&mut response))
        .await
        .unwrap();
    assert!(matches!(result, Ok(0)) || result.is_err());
    let (_socket, _) = fixture.authenticate().await;
    fixture.finish().await;
}

#[tokio::test]
async fn leading_blank_lines_keep_the_upgrade_deadline() {
    let fixture = Fixture::new().await;
    let mut stream = TcpStream::connect(address(&fixture)).await.unwrap();
    stream.write_all(b"\r\n\r\n").await.unwrap();
    tokio::time::sleep(Duration::from_millis(20)).await;
    tokio::time::pause();
    tokio::time::advance(Duration::from_secs(5)).await;
    tokio::time::resume();
    let mut response = [0; 128];
    let result = tokio::time::timeout(Duration::from_secs(2), stream.read(&mut response))
        .await
        .unwrap();
    assert!(matches!(result, Ok(0)) || result.is_err());
    fixture.finish().await;
}

#[tokio::test]
async fn oversized_headers_are_dropped_before_websocket_authentication() {
    let fixture = Fixture::new().await;
    let mut stream = TcpStream::connect(address(&fixture)).await.unwrap();
    let request = format!(
        "GET /connector/v1 HTTP/1.1\r\nX-Padding: {}",
        "a".repeat(9000)
    );
    stream.write_all(request.as_bytes()).await.unwrap();
    let mut response = [0; 128];
    let result = tokio::time::timeout(Duration::from_secs(2), stream.read(&mut response))
        .await
        .unwrap();
    assert!(matches!(result, Ok(0)) || result.is_err());
    fixture.finish().await;
}

#[tokio::test]
async fn accepted_connections_are_bounded_before_upgrade() {
    let fixture = Fixture::new().await;
    let mut stalled = Vec::new();
    for _ in 0..9 {
        let mut stream = TcpStream::connect(address(&fixture)).await.unwrap();
        stream.write_all(b"GET /").await.unwrap();
        stalled.push(stream);
    }
    let mut request = fixture.address.clone().into_client_request().unwrap();
    request
        .headers_mut()
        .insert("origin", ORIGIN.parse().unwrap());
    let mut connecting = Box::pin(connect_async(request));
    assert!(
        tokio::time::timeout(Duration::from_millis(100), &mut connecting)
            .await
            .is_err()
    );
    drop(stalled);
    let (_socket, _) = tokio::time::timeout(Duration::from_secs(2), connecting)
        .await
        .unwrap()
        .unwrap();
    fixture.finish().await;
}

fn address(fixture: &Fixture) -> &str {
    fixture
        .address
        .strip_prefix("ws://")
        .unwrap()
        .strip_suffix("/connector/v1")
        .unwrap()
}
