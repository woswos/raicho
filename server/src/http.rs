use std::path::Path;
use std::sync::Arc;

use axum::extract::State;
use axum::http::{HeaderValue, StatusCode, header::CACHE_CONTROL};
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;
use tower_http::services::ServeDir;
use tower_http::set_header::SetResponseHeaderLayer;

use crate::persistence::Database;

#[derive(Serialize)]
struct Health {
    status: &'static str,
}

#[derive(Serialize)]
struct DatabaseStatus {
    status: &'static str,
    engine: &'static str,
    version: String,
}

#[derive(Serialize)]
struct BackendStatus {
    status: &'static str,
    kind: &'static str,
}

#[derive(Serialize)]
struct Status {
    status: &'static str,
    database: DatabaseStatus,
    backend: BackendStatus,
    version: &'static str,
}

pub fn router(database: Arc<Database>, web_dir: &Path) -> Router {
    let health = Router::new()
        .route("/live", get(live))
        .route("/ready", get(ready))
        .fallback(not_found);
    let api = Router::new()
        .route("/status", get(status))
        .fallback(not_found);
    Router::new()
        .nest("/health", health)
        .nest("/api", api)
        .fallback_service(ServeDir::new(web_dir))
        .with_state(database)
        .layer(SetResponseHeaderLayer::overriding(
            CACHE_CONTROL,
            HeaderValue::from_static("no-store"),
        ))
}

async fn live() -> Json<Health> {
    Json(Health { status: "alive" })
}

async fn readiness(database: &Database) -> (StatusCode, &'static str) {
    if database.check().await.is_ok() {
        (StatusCode::OK, "ready")
    } else {
        (StatusCode::SERVICE_UNAVAILABLE, "unavailable")
    }
}

async fn ready(State(database): State<Arc<Database>>) -> (StatusCode, Json<Health>) {
    let (code, status) = readiness(&database).await;
    (code, Json(Health { status }))
}

async fn status(State(database): State<Arc<Database>>) -> (StatusCode, Json<Status>) {
    let (code, status) = readiness(&database).await;
    (
        code,
        Json(Status {
            status,
            database: DatabaseStatus {
                status,
                engine: "sqlite",
                version: database.version().into(),
            },
            backend: BackendStatus {
                status: "unconfigured",
                kind: "thunderbird",
            },
            version: env!("CARGO_PKG_VERSION"),
        }),
    )
}

async fn not_found() -> StatusCode {
    StatusCode::NOT_FOUND
}
