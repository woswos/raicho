use std::collections::HashMap;
use std::sync::{Arc, LazyLock};

use axum::Router;
use axum::body::{Body, to_bytes};
use axum::http::{HeaderMap, Method, Request, StatusCode};
use raicho_server::connector::Connector;
use raicho_server::persistence::Database;
use raicho_server::public_origin::PublicOrigin;
use serde_json::{Value, json};
use tempfile::TempDir;
use tower::ServiceExt;

use super::PUBLIC_ORIGIN;
use super::mock_backend::MockBackend;

pub const PASSWORD: &str = "correct horse battery";

const DOCUMENTS: [&str; 6] = [
    "SessionDocument",
    "PreferencesDocument",
    "AccountsDocument",
    "MailboxesDocument",
    "MessagesDocument",
    "ErrorDocument",
];

static VALIDATORS: LazyLock<HashMap<&str, jsonschema::Validator>> = LazyLock::new(|| {
    let schema: Value = serde_json::from_str(include_str!("../../../../protocol/schema/api.schema.json")).unwrap();
    DOCUMENTS
        .into_iter()
        .map(|document| {
            let definition = json!({
                "definitions": schema["definitions"],
                "allOf": [{ "$ref": format!("#/definitions/{document}") }],
            });
            let validator = jsonschema::options()
                .with_draft(jsonschema::Draft::Draft7)
                .build(&definition)
                .unwrap();
            (document, validator)
        })
        .collect()
});

// Logout answers 204, and unknown paths and methods fall through to axum's empty 404 and 405.
const BODYLESS: [StatusCode; 3] = [
    StatusCode::NO_CONTENT,
    StatusCode::NOT_FOUND,
    StatusCode::METHOD_NOT_ALLOWED,
];

/// The API schema document that a successful response from this path must match.
fn document(path: &str) -> &'static str {
    match path {
        "/api/session" => "SessionDocument",
        "/api/preferences" => "PreferencesDocument",
        "/api/mail/accounts" => "AccountsDocument",
        path if path.starts_with("/api/mail/accounts/") && path.ends_with("/mailboxes") => "MailboxesDocument",
        path if path.starts_with("/api/mail/mailboxes/") && path.ends_with("/messages") => "MessagesDocument",
        path if path.starts_with("/api/mail/cursors/") => "MessagesDocument",
        path => panic!("{path} returns no API document"),
    }
}

pub struct Response {
    pub status: StatusCode,
    pub headers: HeaderMap,
    pub body: Value,
}

/// A router over a temporary database and the mock backend, driven like a browser page.
pub struct Browser {
    pub router: Router,
    pub database: Arc<Database>,
    pub backend: Arc<MockBackend>,
    directory: TempDir,
}

impl Browser {
    pub async fn new() -> Self {
        let browser = Self::open(tempfile::tempdir().unwrap()).await;
        let hash = raicho_server::login::hash_password(PASSWORD.as_bytes()).unwrap();
        browser.database.set_login_password(&hash, 0).await.unwrap();
        browser
    }

    async fn open(directory: TempDir) -> Self {
        let database = Arc::new(Database::open(directory.path()).await.unwrap());
        let backend = Arc::new(MockBackend::default());
        let router = raicho_server::router(
            Arc::clone(&database),
            directory.path(),
            Connector::new(Arc::clone(&database)),
            Arc::clone(&backend),
            PublicOrigin::parse(PUBLIC_ORIGIN).unwrap(),
        );
        Self {
            router,
            database,
            backend,
            directory,
        }
    }

    /// Restarts the server on the same database.
    pub async fn restart(self) -> Self {
        let Self {
            router,
            database,
            directory,
            ..
        } = self;
        drop(router);
        database.close().await;
        drop(database);
        Self::open(directory).await
    }

    pub async fn send(&self, method: Method, path: &str, cookie: Option<&str>, body: Option<&str>) -> Response {
        let mut request = Request::builder().method(method.clone()).uri(path);
        if method != Method::GET {
            request = request
                .header("Origin", PUBLIC_ORIGIN)
                .header("Sec-Fetch-Site", "same-origin")
                .header("Content-Type", "application/json");
        }
        if let Some(cookie) = cookie {
            request = request.header("Cookie", cookie);
        }
        let body = body.map_or_else(Body::empty, |body| Body::from(body.to_owned()));
        self.raw(request.body(body).unwrap()).await
    }

    pub async fn raw(&self, request: Request<Body>) -> Response {
        let path = request.uri().path().to_owned();
        let method = request.method().clone();
        let response = self.router.clone().oneshot(request).await.unwrap();
        let status = response.status();
        let headers = response.headers().clone();
        let bytes = to_bytes(response.into_body(), 1 << 20).await.unwrap();
        if bytes.is_empty() {
            assert!(
                method == Method::HEAD || BODYLESS.contains(&status),
                "{path} returned {status} without a body"
            );
            return Response {
                status,
                headers,
                body: Value::Null,
            };
        }
        let body = serde_json::from_slice(&bytes).unwrap();
        let document = if status.is_success() {
            document(&path)
        } else {
            "ErrorDocument"
        };
        assert!(
            VALIDATORS[document].is_valid(&body),
            "{path} returned {body}, not a {document}"
        );
        Response { status, headers, body }
    }

    pub async fn get(&self, path: &str, cookie: &str) -> Response {
        self.send(Method::GET, path, Some(cookie), None).await
    }

    pub async fn sign_in(&self) -> String {
        let response = self
            .send(
                Method::POST,
                "/api/session",
                None,
                Some(&format!("{{\"password\":\"{PASSWORD}\"}}")),
            )
            .await;
        assert_eq!(response.status, StatusCode::OK, "{}", response.body);
        let cookie = response.headers["set-cookie"].to_str().unwrap();
        cookie.split(';').next().unwrap().to_owned()
    }

    pub fn data_dir(&self) -> &std::path::Path {
        self.directory.path()
    }

    pub async fn finish(self) {
        self.database.close().await;
    }
}
