use std::sync::{Arc, LazyLock};

use axum::Router;
use axum::body::{Body, to_bytes};
use axum::http::{HeaderMap, Method, Request, StatusCode};
use raicho_server::connector::Connector;
use raicho_server::persistence::Database;
use raicho_server::public_origin::PublicOrigin;
use serde_json::Value;
use tempfile::TempDir;
use tower::ServiceExt;

use super::PUBLIC_ORIGIN;
use super::mock_backend::MockBackend;

pub const PASSWORD: &str = "correct horse battery";

static SCHEMA: LazyLock<jsonschema::Validator> = LazyLock::new(|| {
    let schema: Value = serde_json::from_str(include_str!("../../../../protocol/schema/api.schema.json")).unwrap();
    jsonschema::options()
        .with_draft(jsonschema::Draft::Draft7)
        .build(&schema)
        .unwrap()
});

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
        let response = self.router.clone().oneshot(request).await.unwrap();
        let status = response.status();
        let headers = response.headers().clone();
        let bytes = to_bytes(response.into_body(), 1 << 20).await.unwrap();
        let body = if bytes.is_empty() {
            Value::Null
        } else {
            serde_json::from_slice(&bytes).unwrap()
        };
        if !body.is_null() {
            assert!(SCHEMA.is_valid(&body), "{body} violates the API schema");
        }
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
