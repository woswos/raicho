use std::sync::atomic::Ordering;

use axum::http::{Method, StatusCode};
use serde_json::json;

use crate::support::browser::Browser;
use crate::support::mock_backend::{SECOND_PAGE, SUBJECT};

#[tokio::test]
async fn the_mock_backend_serves_accounts_mailboxes_and_paginated_summaries() {
    let browser = Browser::new().await;
    let session = browser.sign_in().await;
    let accounts = browser.get("/api/mail/accounts", &session).await;
    assert_eq!(accounts.status, StatusCode::OK);
    assert_eq!(
        accounts.body["accounts"][0]["identities"][0]["email"],
        "zoe@raicho.test"
    );
    let mailboxes = browser.get("/api/mail/accounts/mock.account/mailboxes", &session).await;
    assert_eq!(mailboxes.body["truncated"], false);
    assert_eq!(
        mailboxes.body["mailboxes"][1],
        json!({"id":"mock.projects","name":"Projekte","parent":"mock.inbox"})
    );

    let first = browser.get("/api/mail/mailboxes/mock.inbox/messages", &session).await;
    assert_eq!(first.body["messages"].as_array().unwrap().len(), 2);
    assert_eq!(first.body["messages"][0]["subject"], SUBJECT);
    let cursor = first.body["cursor"].as_str().unwrap().to_owned();
    assert_ne!(cursor, SECOND_PAGE);
    let second = browser.get(&format!("/api/mail/cursors/{cursor}"), &session).await;
    assert_eq!(second.body["messages"].as_array().unwrap().len(), 1);
    assert!(second.body.get("cursor").is_none());
    let reused = browser.get(&format!("/api/mail/cursors/{cursor}"), &session).await;
    assert_eq!(reused.status, StatusCode::CONFLICT);
    assert_eq!(reused.body, json!({"error": "stale_cursor"}));
    browser.finish().await;
}

#[tokio::test]
async fn cursors_belong_to_their_session_and_logout_closes_them() {
    let browser = Browser::new().await;
    let owner = browser.sign_in().await;
    let other = browser.sign_in().await;
    let page = browser.get("/api/mail/mailboxes/mock.inbox/messages", &owner).await;
    let cursor = page.body["cursor"].as_str().unwrap().to_owned();
    let stolen = browser.get(&format!("/api/mail/cursors/{cursor}"), &other).await;
    assert_eq!(stolen.body, json!({"error": "stale_cursor"}));
    browser.send(Method::DELETE, "/api/session", Some(&owner), None).await;
    tokio::task::yield_now().await;
    tokio::time::sleep(std::time::Duration::from_millis(20)).await;
    assert_eq!(*browser.backend.closed.lock().unwrap(), [SECOND_PAGE]);
    browser.finish().await;
}

#[tokio::test]
async fn backend_failures_keep_their_categories_and_handles_are_checked() {
    let browser = Browser::new().await;
    let session = browser.sign_in().await;
    for (path, status, error) in [
        (
            "/api/mail/accounts/unknown/mailboxes",
            StatusCode::CONFLICT,
            "stale_handle",
        ),
        (
            "/api/mail/accounts/bad%20handle/mailboxes",
            StatusCode::BAD_REQUEST,
            "invalid_request",
        ),
        (
            "/api/mail/mailboxes/mock.projects/messages",
            StatusCode::CONFLICT,
            "stale_handle",
        ),
    ] {
        let response = browser.get(path, &session).await;
        assert_eq!(
            (response.status, response.body),
            (status, json!({"error": error})),
            "{path}"
        );
    }
    browser.backend.disconnected.store(true, Ordering::SeqCst);
    let response = browser.get("/api/mail/accounts", &session).await;
    assert_eq!(response.status, StatusCode::SERVICE_UNAVAILABLE);
    assert_eq!(response.body, json!({"error": "backend_disconnected"}));
    assert_eq!(browser.get("/api/session", &session).await.status, StatusCode::OK);
    browser.finish().await;
}

#[tokio::test]
async fn mail_returned_to_the_browser_never_reaches_the_database() {
    let browser = Browser::new().await;
    let session = browser.sign_in().await;
    browser.get("/api/mail/accounts", &session).await;
    browser.get("/api/mail/accounts/mock.account/mailboxes", &session).await;
    let page = browser.get("/api/mail/mailboxes/mock.inbox/messages", &session).await;
    browser
        .get(
            &format!("/api/mail/cursors/{}", page.body["cursor"].as_str().unwrap()),
            &session,
        )
        .await;
    let tables: Vec<String> = sqlx::query_scalar(
        "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT GLOB 'sqlite_*' ORDER BY name",
    )
    .fetch_all(browser.database.pool())
    .await
    .unwrap();
    assert_eq!(
        tables,
        [
            "_sqlx_migrations",
            "browser_sessions",
            "connector_credentials",
            "login_password",
            "preferences"
        ]
    );
    for entry in std::fs::read_dir(browser.data_dir()).unwrap() {
        let bytes = std::fs::read(entry.unwrap().path()).unwrap_or_default();
        for fictional in [SUBJECT, "Fictional account", "Projekte", "zoe@raicho.test", "mock."] {
            assert!(
                !bytes
                    .windows(fictional.len())
                    .any(|window| window == fictional.as_bytes()),
                "The data directory holds {fictional}"
            );
        }
    }
    browser.finish().await;
}
