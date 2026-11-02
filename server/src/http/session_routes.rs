use axum::Json;
use axum::body::Bytes;
use axum::extract::State;
use axum::http::StatusCode;
use axum::http::header::SET_COOKIE;
use axum::response::{IntoResponse, Response};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use super::ApplicationState;
use super::api_error::{ApiError, rate_limited};
use super::guard::BrowserSession;
use crate::login::{LoginFailure, MAXIMUM_PASSWORD_BYTES};
use crate::mail::MailBackend;
use crate::persistence::SESSION_LIFETIME_SECONDS;
use crate::public_origin::PublicOrigin;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SignIn {
    password: String,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum Theme {
    System,
    Light,
    Dark,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Preferences {
    theme: Theme,
}

fn authenticated() -> Json<Value> {
    Json(json!({ "authenticated": true }))
}

pub async fn current(_session: BrowserSession) -> Json<Value> {
    authenticated()
}

pub async fn sign_in<Backend: MailBackend>(State(state): State<ApplicationState<Backend>>, body: Bytes) -> Response {
    let Ok(SignIn { password }) = serde_json::from_slice(&body) else {
        return ApiError::InvalidRequest.into_response();
    };
    if password.len() > MAXIMUM_PASSWORD_BYTES {
        return ApiError::InvalidPassword.into_response();
    }
    match state.login.sign_in(&state.database, password.into_bytes()).await {
        Ok(token) => (
            [(
                SET_COOKIE,
                session_cookie(&state.origin, &token, SESSION_LIFETIME_SECONDS),
            )],
            authenticated(),
        )
            .into_response(),
        Err(LoginFailure::Throttled(wait)) => rate_limited(wait),
        Err(LoginFailure::InvalidPassword) => ApiError::InvalidPassword.into_response(),
        Err(LoginFailure::Unconfigured) => ApiError::LoginUnconfigured.into_response(),
        Err(LoginFailure::Unavailable) => ApiError::StorageUnavailable.into_response(),
    }
}

pub async fn sign_out<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    session: Result<BrowserSession, ApiError>,
) -> Response {
    if let Ok(BrowserSession(digest)) = session {
        if state.database.delete_browser_session(&digest).await.is_err() {
            return ApiError::StorageUnavailable.into_response();
        }
        state.close_cursors(state.cursors.end_session(&digest));
    }
    (
        StatusCode::NO_CONTENT,
        [(SET_COOKIE, session_cookie(&state.origin, "", 0))],
    )
        .into_response()
}

fn session_cookie(origin: &PublicOrigin, token: &str, max_age: i64) -> String {
    format!(
        "{}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}{}",
        origin.cookie_name(),
        if origin.is_secure() { "; Secure" } else { "" }
    )
}

pub async fn read_preferences<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    _session: BrowserSession,
) -> Response {
    match state.database.preference("theme").await {
        Ok(value) => {
            let theme = value
                .and_then(|value| serde_json::from_value(Value::String(value)).ok())
                .unwrap_or(Theme::System);
            Json(Preferences { theme }).into_response()
        }
        Err(_) => ApiError::StorageUnavailable.into_response(),
    }
}

pub async fn write_preferences<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    _session: BrowserSession,
    body: Bytes,
) -> Response {
    let Ok(preferences) = serde_json::from_slice::<Preferences>(&body) else {
        return ApiError::InvalidRequest.into_response();
    };
    let Ok(Value::String(theme)) = serde_json::to_value(preferences.theme) else {
        return ApiError::InvalidRequest.into_response();
    };
    match state.database.set_preference("theme", &theme).await {
        Ok(()) => Json(preferences).into_response(),
        Err(_) => ApiError::StorageUnavailable.into_response(),
    }
}
