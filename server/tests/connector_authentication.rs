mod support;

use raicho_protocol::diagnostics_generated::{BackendError, BackendState};
use std::time::Duration;

use futures_util::SinkExt;
use raicho_server::persistence::CredentialStore;
use serde_json::json;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::{Message, client::IntoClientRequest};

use support::{Fixture, ORIGIN, authentication, receive, receive_within};

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
    let error = receive_within(&mut socket, Duration::from_secs(12)).await;
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
    let trailing_slash = format!("{ORIGIN}/");
    let uppercase = ORIGIN.to_uppercase();
    let joined = format!("{ORIGIN}, {ORIGIN}");
    for (suffix, origins, protocol) in [
        ("?token=redacted", vec![ORIGIN], None),
        ("/extra", vec![ORIGIN], None),
        ("", vec![], None),
        ("", vec!["https://example.com"], None),
        ("", vec!["moz-extension://invalid"], None),
        ("", vec![trailing_slash.as_str()], None),
        ("", vec![uppercase.as_str()], None),
        ("", vec![joined.as_str()], None),
        ("", vec!["null"], None),
        ("", vec![ORIGIN, ORIGIN], None),
        ("", vec![ORIGIN], Some("credential")),
    ] {
        let mut request = format!("{}{suffix}", fixture.address)
            .into_client_request()
            .unwrap();
        for origin in origins {
            request
                .headers_mut()
                .append("Origin", origin.parse().unwrap());
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
