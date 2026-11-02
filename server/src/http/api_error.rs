use std::time::Duration;

use axum::Json;
use axum::http::header::RETRY_AFTER;
use axum::http::{HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use serde::Serialize;
use serde_json::json;

use crate::mail::MailFailure;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ApiError {
    Unauthenticated,
    ForbiddenOrigin,
    InvalidRequest,
    RateLimited,
    InvalidPassword,
    LoginUnconfigured,
    StorageUnavailable,
    BackendDisconnected,
    BackendBusy,
    BackendTimeout,
    StaleHandle,
    StaleCursor,
    Unsupported,
    BackendFailed,
}

impl ApiError {
    fn status(self) -> StatusCode {
        match self {
            Self::Unauthenticated | Self::InvalidPassword => StatusCode::UNAUTHORIZED,
            Self::ForbiddenOrigin => StatusCode::FORBIDDEN,
            Self::InvalidRequest => StatusCode::BAD_REQUEST,
            Self::RateLimited => StatusCode::TOO_MANY_REQUESTS,
            Self::LoginUnconfigured | Self::StorageUnavailable | Self::BackendDisconnected | Self::BackendBusy => {
                StatusCode::SERVICE_UNAVAILABLE
            }
            Self::BackendTimeout => StatusCode::GATEWAY_TIMEOUT,
            Self::StaleHandle | Self::StaleCursor => StatusCode::CONFLICT,
            Self::Unsupported => StatusCode::UNPROCESSABLE_ENTITY,
            Self::BackendFailed => StatusCode::BAD_GATEWAY,
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status(), Json(json!({ "error": self }))).into_response()
    }
}

impl From<MailFailure> for ApiError {
    fn from(failure: MailFailure) -> Self {
        match failure {
            MailFailure::InvalidRequest => Self::InvalidRequest,
            MailFailure::BackendDisconnected => Self::BackendDisconnected,
            MailFailure::BackendBusy => Self::BackendBusy,
            MailFailure::BackendTimeout => Self::BackendTimeout,
            MailFailure::StaleHandle => Self::StaleHandle,
            MailFailure::StaleCursor => Self::StaleCursor,
            MailFailure::Unsupported => Self::Unsupported,
            MailFailure::BackendFailed => Self::BackendFailed,
        }
    }
}

pub fn rate_limited(wait: Duration) -> Response {
    let mut response = ApiError::RateLimited.into_response();
    let seconds = wait.as_secs() + u64::from(wait.subsec_nanos() > 0);
    response
        .headers_mut()
        .insert(RETRY_AFTER, HeaderValue::from(seconds.max(1)));
    response
}
