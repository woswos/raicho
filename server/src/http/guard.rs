use axum::extract::{FromRequestParts, Request, State};
use axum::http::header::{CONTENT_TYPE, COOKIE, ORIGIN};
use axum::http::request::Parts;
use axum::http::{HeaderMap, Method};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};

use super::ApplicationState;
use super::api_error::ApiError;
use crate::login;
use crate::mail::MailBackend;
use crate::persistence::TokenDigest;

// The nested API router sees paths without its `/api` prefix.
const LOGOUT_PATH: &str = "/session";

/// Rejects a request that can change state unless it comes from the deployment's own page.
pub async fn protect_mutations<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    request: Request,
    next: Next,
) -> Response {
    if matches!(*request.method(), Method::GET | Method::HEAD) {
        return next.run(request).await;
    }
    let headers = request.headers();
    let same_origin = headers
        .get(ORIGIN)
        .is_some_and(|origin| origin == state.origin.as_str())
        && headers.get("sec-fetch-site").is_none_or(|site| site == "same-origin");
    if !same_origin {
        return ApiError::ForbiddenOrigin.into_response();
    }
    // Logout has no body, so it is the one mutation without a JSON content type.
    let logout = request.method() == Method::DELETE && request.uri().path() == LOGOUT_PATH;
    if !logout && !is_json(headers) {
        return ApiError::InvalidRequest.into_response();
    }
    next.run(request).await
}

fn is_json(headers: &HeaderMap) -> bool {
    headers
        .get(CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.split(';').next())
        .is_some_and(|media_type| media_type.trim().eq_ignore_ascii_case("application/json"))
}

/// A request that carries a current session cookie.
pub struct BrowserSession(pub TokenDigest);

impl<Backend: MailBackend> FromRequestParts<ApplicationState<Backend>> for BrowserSession {
    type Rejection = ApiError;

    async fn from_request_parts(parts: &mut Parts, state: &ApplicationState<Backend>) -> Result<Self, Self::Rejection> {
        let token = session_token(&parts.headers, state.origin.cookie_name()).ok_or(ApiError::Unauthenticated)?;
        let digest = login::digest(&token);
        match state.database.use_browser_session(&digest, login::now()).await {
            Ok(true) => Ok(Self(digest)),
            Ok(false) => Err(ApiError::Unauthenticated),
            Err(_) => Err(ApiError::StorageUnavailable),
        }
    }
}

fn session_token(headers: &HeaderMap, name: &str) -> Option<String> {
    headers
        .get_all(COOKIE)
        .iter()
        .filter_map(|value| value.to_str().ok())
        .flat_map(|value| value.split(';'))
        .filter_map(|pair| pair.trim().split_once('='))
        .find(|(cookie, _)| *cookie == name)
        .map(|(_, token)| token.to_owned())
        .filter(|token| login::is_token(token))
}
