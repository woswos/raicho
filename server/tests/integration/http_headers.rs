use std::fs;
use std::sync::Arc;

use axum::body::Body;
use axum::http::Request;
use raicho_server::persistence::Database;
use tempfile::tempdir;
use tower::ServiceExt;

#[tokio::test]
async fn every_response_carries_the_security_headers() {
    let directory = tempdir().unwrap();
    fs::write(directory.path().join("index.html"), "<h1>Raicho diagnostics</h1>").unwrap();
    let database = Arc::new(Database::open(directory.path()).await.unwrap());
    let application = crate::support::application(Arc::clone(&database), directory.path());
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
