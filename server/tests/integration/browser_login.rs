use axum::body::Body;
use axum::http::{Method, Request, StatusCode};
use raicho_server::login;
use raicho_server::persistence::{
    MAXIMUM_SESSIONS, SESSION_IDLE_SECONDS, SESSION_LIFETIME_SECONDS, SESSION_TOUCH_SECONDS,
};
use serde_json::json;

use crate::support::PUBLIC_ORIGIN;
use crate::support::browser::{Browser, PASSWORD};

const PROTECTED: [&str; 5] = [
    "/api/session",
    "/api/preferences",
    "/api/mail/accounts",
    "/api/mail/accounts/mock.account/mailboxes",
    "/api/mail/mailboxes/mock.inbox/messages",
];

#[tokio::test]
async fn login_issues_a_protected_session_cookie_and_logout_ends_it() {
    let browser = Browser::new().await;
    let response = browser
        .send(
            Method::POST,
            "/api/session",
            None,
            Some(&format!("{{\"password\":\"{PASSWORD}\"}}")),
        )
        .await;
    assert_eq!(response.status, StatusCode::OK);
    assert_eq!(response.body, json!({"authenticated": true}));
    assert_eq!(response.headers["cache-control"], "no-store");
    let cookie = response.headers["set-cookie"].to_str().unwrap();
    assert!(cookie.starts_with("raicho_session="));
    assert!(cookie.ends_with("; Path=/; HttpOnly; SameSite=Strict; Max-Age=2592000"));
    let session = cookie.split(';').next().unwrap().to_owned();
    assert_eq!(browser.get("/api/session", &session).await.status, StatusCode::OK);

    let logout = browser.send(Method::DELETE, "/api/session", Some(&session), None).await;
    assert_eq!(logout.status, StatusCode::NO_CONTENT);
    assert!(
        logout.headers["set-cookie"]
            .to_str()
            .unwrap()
            .contains("raicho_session=; ")
    );
    assert!(logout.headers["set-cookie"].to_str().unwrap().contains("Max-Age=0"));
    assert_eq!(
        browser.get("/api/session", &session).await.status,
        StatusCode::UNAUTHORIZED
    );
    browser.finish().await;
}

#[tokio::test]
async fn every_protected_route_rejects_missing_forged_and_malformed_sessions() {
    let browser = Browser::new().await;
    for path in PROTECTED
        .into_iter()
        .chain(["/api/mail/cursors/00000000000000000000000000000000"])
    {
        for cookie in [
            None,
            Some(format!("raicho_session={}", "a".repeat(64))),
            Some("raicho_session=short".to_owned()),
            Some(format!("__Host-raicho_session={}", "a".repeat(64))),
        ] {
            let response = browser.send(Method::GET, path, cookie.as_deref(), None).await;
            assert_eq!(response.status, StatusCode::UNAUTHORIZED, "{path}");
            assert_eq!(response.body, json!({"error": "unauthenticated"}));
        }
    }
    assert_eq!(browser.backend.closed.lock().unwrap().len(), 0);
    browser.finish().await;
}

#[tokio::test]
async fn mutations_require_the_public_origin_a_same_origin_fetch_and_json() {
    let browser = Browser::new().await;
    let body = format!("{{\"password\":\"{PASSWORD}\"}}");
    for (origin, site, content_type, expected) in [
        (None, None, Some("application/json"), "forbidden_origin"),
        (
            Some("https://attacker.example"),
            None,
            Some("application/json"),
            "forbidden_origin",
        ),
        (
            Some("http://127.0.0.1:8080"),
            None,
            Some("application/json"),
            "forbidden_origin",
        ),
        (
            Some(PUBLIC_ORIGIN),
            Some("cross-site"),
            Some("application/json"),
            "forbidden_origin",
        ),
        (
            Some(PUBLIC_ORIGIN),
            Some("same-origin"),
            Some("text/plain"),
            "invalid_request",
        ),
        (Some(PUBLIC_ORIGIN), None, None, "invalid_request"),
    ] {
        let mut request = Request::builder().method(Method::POST).uri("/api/session");
        for (name, value) in [
            ("Origin", origin),
            ("Sec-Fetch-Site", site),
            ("Content-Type", content_type),
        ] {
            if let Some(value) = value {
                request = request.header(name, value);
            }
        }
        let response = browser.raw(request.body(Body::from(body.clone())).unwrap()).await;
        assert_eq!(
            response.body,
            json!({"error": expected}),
            "{origin:?} {site:?} {content_type:?}"
        );
        assert!(response.headers.get("set-cookie").is_none());
    }
    let mut request = Request::builder()
        .method(Method::POST)
        .uri("/api/session")
        .header("Origin", PUBLIC_ORIGIN)
        .header("Content-Type", "application/json; charset=utf-8");
    request = request.header("Cookie", "unrelated=1");
    let accepted = browser.raw(request.body(Body::from(body)).unwrap()).await;
    assert_eq!(accepted.status, StatusCode::OK);
    browser.finish().await;
}

#[tokio::test]
async fn only_logout_skips_the_content_type_and_it_needs_the_public_origin() {
    let browser = Browser::new().await;
    let session = browser.sign_in().await;
    let logout = |origin: Option<&str>| {
        let mut request = Request::builder()
            .method(Method::DELETE)
            .uri("/api/session")
            .header("Cookie", &session);
        if let Some(origin) = origin {
            request = request.header("Origin", origin);
        }
        request.body(Body::empty()).unwrap()
    };
    let refused = browser.raw(logout(Some("https://attacker.example"))).await;
    assert_eq!(refused.body, json!({"error": "forbidden_origin"}));
    assert_eq!(browser.get("/api/session", &session).await.status, StatusCode::OK);
    let other = Request::builder()
        .method(Method::DELETE)
        .uri("/api/preferences")
        .header("Origin", PUBLIC_ORIGIN)
        .header("Cookie", &session)
        .body(Body::empty())
        .unwrap();
    assert_eq!(browser.raw(other).await.body, json!({"error": "invalid_request"}));
    assert_eq!(
        browser.raw(logout(Some(PUBLIC_ORIGIN))).await.status,
        StatusCode::NO_CONTENT
    );
    assert_eq!(
        browser.get("/api/session", &session).await.status,
        StatusCode::UNAUTHORIZED
    );
    browser.finish().await;
}

#[tokio::test]
async fn wrong_passwords_are_throttled_and_an_unconfigured_login_is_reported() {
    let browser = Browser::new().await;
    for _ in 0..5 {
        let response = browser
            .send(
                Method::POST,
                "/api/session",
                None,
                Some("{\"password\":\"wrong password!\"}"),
            )
            .await;
        assert_eq!(response.status, StatusCode::UNAUTHORIZED);
        assert_eq!(response.body, json!({"error": "invalid_password"}));
    }
    let throttled = browser
        .send(
            Method::POST,
            "/api/session",
            None,
            Some(&format!("{{\"password\":\"{PASSWORD}\"}}")),
        )
        .await;
    assert_eq!(throttled.status, StatusCode::TOO_MANY_REQUESTS);
    assert!(
        throttled.headers["retry-after"]
            .to_str()
            .unwrap()
            .parse::<u64>()
            .unwrap()
            <= 60
    );
    for body in [
        "{}",
        "{\"password\":1}",
        "{\"password\":\"x\",\"user\":\"x\"}",
        "not json",
    ] {
        let response = browser.send(Method::POST, "/api/session", None, Some(body)).await;
        assert_eq!(response.body, json!({"error": "invalid_request"}), "{body}");
    }
    let oversized = format!("{{\"password\":\"{}\"}}", "a".repeat(1025));
    let response = browser.send(Method::POST, "/api/session", None, Some(&oversized)).await;
    assert_eq!(response.body, json!({"error": "invalid_password"}));

    let browser = browser.restart().await;
    browser.database.revoke_browser_sessions().await.unwrap();
    sqlx::query("DELETE FROM login_password")
        .execute(browser.database.pool())
        .await
        .unwrap();
    let response = browser
        .send(
            Method::POST,
            "/api/session",
            None,
            Some(&format!("{{\"password\":\"{PASSWORD}\"}}")),
        )
        .await;
    assert_eq!(response.status, StatusCode::SERVICE_UNAVAILABLE);
    assert_eq!(response.body, json!({"error": "login_unconfigured"}));
    browser.finish().await;
}

#[tokio::test]
async fn concurrent_sessions_survive_restart_until_revoked_or_reset() {
    let browser = Browser::new().await;
    let first = browser.sign_in().await;
    let second = browser.sign_in().await;
    assert_ne!(first, second);
    browser.send(Method::DELETE, "/api/session", Some(&first), None).await;
    assert_eq!(
        browser.get("/api/session", &first).await.status,
        StatusCode::UNAUTHORIZED
    );
    assert_eq!(browser.get("/api/session", &second).await.status, StatusCode::OK);

    let browser = browser.restart().await;
    assert_eq!(browser.get("/api/session", &second).await.status, StatusCode::OK);
    browser.database.revoke_browser_sessions().await.unwrap();
    assert_eq!(
        browser.get("/api/session", &second).await.status,
        StatusCode::UNAUTHORIZED
    );

    let third = browser.sign_in().await;
    let hash = login::hash_password(b"another long password").unwrap();
    browser.database.set_login_password(&hash, login::now()).await.unwrap();
    assert_eq!(
        browser.get("/api/session", &third).await.status,
        StatusCode::UNAUTHORIZED
    );
    browser.finish().await;
}

#[tokio::test]
async fn sessions_expire_when_idle_or_old_and_the_oldest_are_removed() {
    let browser = Browser::new().await;
    let database = &browser.database;
    let digest = login::digest(&"b".repeat(64));
    database.create_browser_session(&digest, 1_000).await.unwrap();
    assert!(
        database
            .use_browser_session(&digest, 1_000 + SESSION_TOUCH_SECONDS)
            .await
            .unwrap()
    );
    let touched = 1_000 + SESSION_TOUCH_SECONDS;
    assert!(
        database
            .use_browser_session(&digest, touched + SESSION_IDLE_SECONDS - 1)
            .await
            .unwrap()
    );
    assert!(
        !database
            .use_browser_session(&digest, 1_000 + SESSION_LIFETIME_SECONDS)
            .await
            .unwrap()
    );
    assert_eq!(database.browser_session_count().await.unwrap(), 0);

    database.create_browser_session(&digest, 1_000).await.unwrap();
    assert!(
        !database
            .use_browser_session(&digest, 1_000 + SESSION_IDLE_SECONDS)
            .await
            .unwrap()
    );

    for index in 0..MAXIMUM_SESSIONS + 3 {
        let digest = login::digest(&format!("{index:064}"));
        database.create_browser_session(&digest, 2_000 + index).await.unwrap();
    }
    assert_eq!(database.browser_session_count().await.unwrap(), MAXIMUM_SESSIONS);
    assert!(
        !database
            .use_browser_session(&login::digest(&format!("{:064}", 0)), 3_000)
            .await
            .unwrap()
    );
    browser.finish().await;
}

#[tokio::test]
async fn the_theme_preference_persists_across_restarts() {
    let browser = Browser::new().await;
    let session = browser.sign_in().await;
    assert_eq!(
        browser.get("/api/preferences", &session).await.body,
        json!({"theme": "system"})
    );
    let update = browser
        .send(
            Method::PUT,
            "/api/preferences",
            Some(&session),
            Some("{\"theme\":\"dark\"}"),
        )
        .await;
    assert_eq!(update.body, json!({"theme": "dark"}));
    for body in ["{\"theme\":\"sepia\"}", "{\"theme\":\"dark\",\"font\":\"x\"}", "{}"] {
        let rejected = browser
            .send(Method::PUT, "/api/preferences", Some(&session), Some(body))
            .await;
        assert_eq!(rejected.body, json!({"error": "invalid_request"}), "{body}");
    }
    let browser = browser.restart().await;
    assert_eq!(
        browser.get("/api/preferences", &session).await.body,
        json!({"theme": "dark"})
    );
    browser.finish().await;
}
