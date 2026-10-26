use std::fs;
use std::sync::Arc;

use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use raicho_server::{connector::Connector, persistence::Database, router};
use serde_json::{Value, json};
use tempfile::tempdir;
use tower::ServiceExt;

#[tokio::test]
async fn diagnostics_report_database_readiness_independently_of_thunderbird() {
    let directory = tempdir().unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(
        Arc::clone(&database),
        directory.path(),
        Connector::new(Arc::clone(&database)),
    );
    for path in ["/health/live", "/health/ready", "/api/status"] {
        let response = application
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()["cache-control"], "no-store");
        if path == "/api/status" {
            let body = to_bytes(response.into_body(), 4096).await.unwrap();
            let status: Value = serde_json::from_slice(&body).unwrap();
            assert_eq!(
                status,
                json!({
                    "status": "ready",
                    "database": {"status": "ready", "engine": "sqlite", "version": "3.51.3"},
                    "backend": {
                        "status": "unconfigured", "kind": "thunderbird",
                        "generation": null, "last_error": null, "heartbeat_count": 0
                    },
                    "version": raicho_server::version::version(),
                    "commit": raicho_server::version::commit()
                })
            );
        }
    }
    database.close().await;
    let response = application
        .clone()
        .oneshot(Request::builder().uri("/health/ready").body(Body::empty()).unwrap())
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    let response = application
        .oneshot(Request::builder().uri("/health/live").body(Body::empty()).unwrap())
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn static_files_are_served_without_api_or_path_traversal_fallbacks() {
    let directory = tempdir().unwrap();
    let web = directory.path().join("web");
    fs::create_dir(&web).unwrap();
    fs::write(web.join("index.html"), "<h1>Raicho diagnostics</h1>").unwrap();
    fs::write(web.join("diagnostics.js"), "document.title='Raicho';").unwrap();
    fs::create_dir(web.join("api")).unwrap();
    fs::write(web.join("api/missing"), "must not shadow API routes").unwrap();
    fs::create_dir(web.join("health")).unwrap();
    fs::write(web.join("health/missing"), "must not shadow health routes").unwrap();
    fs::create_dir(web.join("connector")).unwrap();
    fs::write(web.join("connector/v1"), "must not expose the internal connector").unwrap();
    fs::write(directory.path().join("private.txt"), "not public").unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(Arc::clone(&database), &web, Connector::new(Arc::clone(&database)));
    for path in ["/", "/diagnostics.js"] {
        let response = application
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()["cache-control"], "no-cache", "{path}");
    }
    for path in [
        "/api/missing",
        "/health/missing",
        "/connector/v1",
        "/missing.js",
        "/%2e%2e/private.txt",
    ] {
        let response = application
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::NOT_FOUND, "{path}");
    }
    database.close().await;
}

#[tokio::test]
async fn every_response_carries_the_security_headers() {
    let directory = tempdir().unwrap();
    fs::write(directory.path().join("index.html"), "<h1>Raicho diagnostics</h1>").unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(
        Arc::clone(&database),
        directory.path(),
        Connector::new(Arc::clone(&database)),
    );
    for path in ["/", "/api/status", "/health/live", "/missing.js", "/connector/v1"] {
        let response = application
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        let headers = response.headers();
        assert_eq!(
            headers["content-security-policy"],
            "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'",
            "{path}"
        );
        assert_eq!(headers["x-content-type-options"], "nosniff", "{path}");
        assert_eq!(headers["referrer-policy"], "no-referrer", "{path}");
    }
    database.close().await;
}

#[tokio::test]
async fn status_responses_follow_the_shared_contract() {
    let schema: Value = serde_json::from_str(include_str!("../../../protocol/schema/status.schema.json")).unwrap();
    let contract = jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .build(&schema)
        .unwrap();
    let directory = tempdir().unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(
        Arc::clone(&database),
        directory.path(),
        Connector::new(Arc::clone(&database)),
    );
    for (code, readiness) in [
        (StatusCode::OK, "ready"),
        (StatusCode::SERVICE_UNAVAILABLE, "unavailable"),
    ] {
        if readiness == "unavailable" {
            database.close().await;
        }
        let response = application
            .clone()
            .oneshot(Request::builder().uri("/api/status").body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), code);
        let body = to_bytes(response.into_body(), 4096).await.unwrap();
        let status: Value = serde_json::from_slice(&body).unwrap();
        assert!(contract.is_valid(&status), "{status}");
        assert_eq!(status["status"], readiness);
    }
}
