use std::fs;
use std::sync::Arc;

use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use raicho_server::{persistence::Database, router};
use serde_json::{Value, json};
use tempfile::tempdir;
use tower::ServiceExt;

#[tokio::test]
async fn diagnostics_report_database_readiness_independently_of_thunderbird() {
    let directory = tempdir().unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(Arc::clone(&database), directory.path());
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
                    "backend": {"status": "unconfigured", "kind": "thunderbird"},
                    "version": raicho_server::version::version(),
                    "commit": raicho_server::version::commit()
                })
            );
        }
    }
    database.close().await;
    let response = application
        .clone()
        .oneshot(
            Request::builder()
                .uri("/health/ready")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    let response = application
        .oneshot(
            Request::builder()
                .uri("/health/live")
                .body(Body::empty())
                .unwrap(),
        )
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
    fs::write(directory.path().join("private.txt"), "not public").unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = router(Arc::clone(&database), &web);
    for path in ["/", "/diagnostics.js"] {
        let response = application
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
    }
    for path in [
        "/api/missing",
        "/health/missing",
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
