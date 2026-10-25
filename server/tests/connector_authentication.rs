mod support;

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use raicho_server::credentials::CredentialStore;
use serde_json::json;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::{Message, client::IntoClientRequest};

use support::{Fixture, ORIGIN, authentication, receive};

#[tokio::test]
async fn authentication_registers_one_session_and_replacement_fences_old_cleanup() {
    let fixture = Fixture::new().await;
    assert_eq!(
        fixture.connector.snapshot().await.status,
        BackendState::Disconnected
    );
    let (mut first, first_welcome) = fixture.authenticate().await;
    let (mut replacement, next_welcome) = fixture.authenticate().await;
    assert_ne!(first_welcome["generation"], next_welcome["generation"]);
    assert_eq!(receive(&mut first).await["code"], "session_replaced");
    drop(first);
    tokio::time::sleep(Duration::from_millis(20)).await;
    let status = fixture.connector.snapshot().await;
    assert_eq!(status.status, BackendState::Connected);
    assert_eq!(status.generation.unwrap(), next_welcome["generation"]);
    replacement.close(None).await.unwrap();
    tokio::time::sleep(Duration::from_millis(20)).await;
    assert_eq!(
        fixture.connector.snapshot().await.status,
        BackendState::Disconnected
    );
    fixture.finish().await;
}

#[tokio::test]
async fn rejected_credentials_do_not_displace_an_authenticated_session() {
    let fixture = Fixture::new().await;
    let (_active, welcome) = fixture.authenticate().await;
    let mut rejected = fixture.connect().await;
    rejected
        .send(Message::Text(authentication("b").to_string().into()))
        .await
        .unwrap();
    assert_eq!(
        receive(&mut rejected).await["code"],
        "authentication_failed"
    );
    let status = fixture.connector.snapshot().await;
    assert_eq!(status.status, BackendState::Connected);
    assert_eq!(status.generation.unwrap(), welcome["generation"]);
    assert_eq!(status.last_error, None);
    fixture.finish().await;
}

#[tokio::test]
async fn revoked_credentials_remain_revoked_and_are_never_enrolled_by_authentication() {
    let fixture = Fixture::new().await;
    CredentialStore::new(&fixture.database)
        .revoke()
        .await
        .unwrap();
    let mut socket = fixture.connect().await;
    socket
        .send(Message::Text(authentication("a").to_string().into()))
        .await
        .unwrap();
    assert_eq!(receive(&mut socket).await["code"], "authentication_failed");
    assert_eq!(
        fixture.connector.snapshot().await.status,
        BackendState::Revoked
    );
    fixture.finish().await;
}

#[tokio::test]
async fn stalled_credential_storage_is_retryable_rather_than_a_rejection() {
    let fixture = Fixture::new().await;
    let held = fixture.database.pool().acquire().await.unwrap();
    let mut socket = fixture.connect().await;
    socket
        .send(Message::Text(authentication("a").to_string().into()))
        .await
        .unwrap();
    let frame = tokio::time::timeout(Duration::from_secs(12), socket.next())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    let error: serde_json::Value = serde_json::from_str(frame.to_text().unwrap()).unwrap();
    assert_eq!(error["code"], "server_busy");
    drop(held);
    assert_eq!(
        fixture.connector.snapshot().await.last_error,
        Some(BackendError::StorageUnavailable)
    );
    fixture.finish().await;
}

#[tokio::test]
async fn route_requires_exact_path_origin_and_no_query_or_subprotocol() {
    let fixture = Fixture::new().await;
    for (suffix, origin, protocol) in [
        ("?token=redacted", Some(ORIGIN), None),
        ("/extra", Some(ORIGIN), None),
        ("", None, None),
        ("", Some("https://example.com"), None),
        ("", Some("moz-extension://invalid"), None),
        ("", Some(ORIGIN), Some("credential")),
    ] {
        let mut request = format!("{}{suffix}", fixture.address)
            .into_client_request()
            .unwrap();
        if let Some(origin) = origin {
            request
                .headers_mut()
                .insert("Origin", origin.parse().unwrap());
        }
        if let Some(protocol) = protocol {
            request
                .headers_mut()
                .insert("Sec-WebSocket-Protocol", protocol.parse().unwrap());
        }
        assert!(connect_async(request).await.is_err());
    }
    fixture.finish().await;
}

#[tokio::test]
async fn authentication_rejects_version_direction_duplicate_and_oversized_messages() {
    let fixture = Fixture::new().await;
    let mut unsupported = authentication("a");
    unsupported["protocol_version"] = json!(2);
    for (frame, expected) in [
        (unsupported.to_string(), "incompatible_version"),
        (
            "{\"type\":\"authenticate\",\"type\":\"authenticate\"}".into(),
            "invalid_message",
        ),
        (" ".repeat(4097), "message_too_large"),
        (
            json!({"type":"pong","protocol_version":1,"generation":"0".repeat(32),"sequence":1})
                .to_string(),
            "unexpected_message",
        ),
    ] {
        let mut socket = fixture.connect().await;
        socket.send(Message::Text(frame.into())).await.unwrap();
        assert_eq!(receive(&mut socket).await["code"], expected);
    }
    assert_eq!(
        fixture.connector.snapshot().await.status,
        BackendState::Disconnected
    );
    fixture.finish().await;
}
