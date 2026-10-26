use std::path::Path;
use std::sync::Arc;

use axum::extract::State;
use axum::http::header::{CACHE_CONTROL, CONTENT_SECURITY_POLICY, REFERRER_POLICY, X_CONTENT_TYPE_OPTIONS};
use axum::http::{HeaderValue, StatusCode};
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;
use tower_http::services::ServeDir;
use tower_http::set_header::SetResponseHeaderLayer;

use raicho_protocol::diagnostics_generated::BackendState;

use crate::connector::{BackendStatus, Connector};
use crate::persistence::Database;

const POLICY: &str =
    "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'";

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

#[derive(Clone)]
struct ApplicationState {
    database: Arc<Database>,
    connector: Arc<Connector>,
}

#[derive(Serialize)]
struct Status {
    status: &'static str,
    database: DatabaseStatus,
    backend: BackendStatus,
    version: &'static str,
    commit: &'static str,
}

pub fn router(database: Arc<Database>, web_dir: &Path, connector: Arc<Connector>) -> Router {
    let no_store = SetResponseHeaderLayer::overriding(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    let health = Router::new()
        .route("/live", get(live))
        .route("/ready", get(ready))
        .fallback(not_found)
        .layer(no_store.clone());
    let api = Router::new()
        .route("/status", get(status))
        .fallback(not_found)
        .layer(no_store);
    Router::new()
        .nest("/health", health)
        .nest("/api", api)
        .nest("/connector", Router::new().fallback(not_found))
        .fallback_service(ServeDir::new(web_dir))
        .with_state(ApplicationState { database, connector })
        // Page files keep stable names, so browsers revalidate them after an upgrade.
        .layer(SetResponseHeaderLayer::if_not_present(
            CACHE_CONTROL,
            HeaderValue::from_static("no-cache"),
        ))
        .layer(SetResponseHeaderLayer::overriding(
            CONTENT_SECURITY_POLICY,
            HeaderValue::from_static(POLICY),
        ))
        .layer(SetResponseHeaderLayer::overriding(
            X_CONTENT_TYPE_OPTIONS,
            HeaderValue::from_static("nosniff"),
        ))
        .layer(SetResponseHeaderLayer::overriding(
            REFERRER_POLICY,
            HeaderValue::from_static("no-referrer"),
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

async fn ready(State(state): State<ApplicationState>) -> (StatusCode, Json<Health>) {
    let (code, status) = readiness(&state.database).await;
    (code, Json(Health { status }))
}

async fn status(State(state): State<ApplicationState>) -> (StatusCode, Json<Status>) {
    let database = &state.database;
    let backend = state.connector.snapshot().await;
    // The snapshot's credential read already proves that the database responds.
    let (code, status) = if backend.status == BackendState::Unavailable {
        (StatusCode::SERVICE_UNAVAILABLE, "unavailable")
    } else {
        (StatusCode::OK, "ready")
    };
    (
        code,
        Json(Status {
            status,
            database: DatabaseStatus {
                status,
                engine: "sqlite",
                version: database.version().into(),
            },
            backend,
            version: crate::version::version(),
            commit: crate::version::commit(),
        }),
    )
}

async fn not_found() -> StatusCode {
    StatusCode::NOT_FOUND
}
