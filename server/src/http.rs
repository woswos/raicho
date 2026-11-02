mod api_error;
mod cursors;
mod guard;
mod mail_routes;
mod session_routes;

use std::ops::Deref;
use std::path::Path;
use std::sync::Arc;

use axum::extract::{DefaultBodyLimit, State};
use axum::http::header::{CACHE_CONTROL, CONTENT_SECURITY_POLICY, REFERRER_POLICY, X_CONTENT_TYPE_OPTIONS};
use axum::http::{HeaderValue, StatusCode};
use axum::middleware;
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;
use tower_http::services::ServeDir;
use tower_http::set_header::SetResponseHeaderLayer;

use raicho_protocol::diagnostics_generated::BackendState;

use crate::connector::{BackendStatus, Connector};
use crate::login::Login;
use crate::mail::MailBackend;
use crate::persistence::Database;
use crate::public_origin::PublicOrigin;

const POLICY: &str =
    "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'";
// Login and preference bodies are small, and mail routes take no body.
const MAXIMUM_BODY_BYTES: usize = 4096;

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

pub struct Shared<Backend> {
    database: Arc<Database>,
    connector: Arc<Connector>,
    backend: Arc<Backend>,
    origin: PublicOrigin,
    login: Login,
    cursors: cursors::Cursors,
}

pub struct ApplicationState<Backend>(Arc<Shared<Backend>>);

impl<Backend> Clone for ApplicationState<Backend> {
    fn clone(&self) -> Self {
        Self(Arc::clone(&self.0))
    }
}

impl<Backend> Deref for ApplicationState<Backend> {
    type Target = Shared<Backend>;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl<Backend: MailBackend> ApplicationState<Backend> {
    fn close_cursors(&self, cursors: cursors::Released) {
        for cursor in cursors {
            let backend = Arc::clone(&self.backend);
            tokio::spawn(async move { backend.close(&cursor).await });
        }
    }
}

#[derive(Serialize)]
struct Status {
    status: &'static str,
    database: DatabaseStatus,
    backend: BackendStatus,
    version: &'static str,
    commit: &'static str,
}

pub fn router<Backend: MailBackend>(
    database: Arc<Database>,
    web_dir: &Path,
    connector: Arc<Connector>,
    backend: Arc<Backend>,
    origin: PublicOrigin,
) -> Router {
    let state = ApplicationState(Arc::new(Shared {
        database,
        connector,
        backend,
        origin,
        login: Login::default(),
        cursors: cursors::Cursors::default(),
    }));
    let no_store = SetResponseHeaderLayer::overriding(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    let health = Router::new()
        .route("/live", get(live))
        .route("/ready", get(ready::<Backend>))
        .fallback(not_found)
        .layer(no_store.clone());
    let api = Router::new()
        .route("/status", get(status::<Backend>))
        .route(
            "/session",
            get(session_routes::current)
                .post(session_routes::sign_in::<Backend>)
                .delete(session_routes::sign_out::<Backend>),
        )
        .route(
            "/preferences",
            get(session_routes::read_preferences::<Backend>).put(session_routes::write_preferences::<Backend>),
        )
        .route("/mail/accounts", get(mail_routes::accounts::<Backend>))
        .route(
            "/mail/accounts/{account}/mailboxes",
            get(mail_routes::mailboxes::<Backend>),
        )
        .route(
            "/mail/mailboxes/{mailbox}/messages",
            get(mail_routes::messages::<Backend>),
        )
        .route("/mail/cursors/{cursor}", get(mail_routes::next_page::<Backend>))
        .fallback(not_found)
        .layer(middleware::from_fn_with_state(
            state.clone(),
            guard::protect_mutations::<Backend>,
        ))
        .layer(DefaultBodyLimit::max(MAXIMUM_BODY_BYTES))
        .layer(no_store);
    Router::new()
        .nest("/health", health)
        .nest("/api", api)
        .nest("/connector", Router::new().fallback(not_found))
        .fallback_service(ServeDir::new(web_dir))
        .with_state(state)
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

async fn ready<Backend: MailBackend>(State(state): State<ApplicationState<Backend>>) -> (StatusCode, Json<Health>) {
    let (code, status) = readiness(&state.database).await;
    (code, Json(Health { status }))
}

async fn status<Backend: MailBackend>(State(state): State<ApplicationState<Backend>>) -> (StatusCode, Json<Status>) {
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
