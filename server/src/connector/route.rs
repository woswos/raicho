use std::sync::Arc;

use axum::Router;
use axum::extract::Request;
use axum::extract::{State, WebSocketUpgrade};
use axum::http::{HeaderMap, Method, StatusCode, Uri};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use raicho_protocol::limits_generated::{AUTHENTICATION_MAX_BYTES, CONTROL_MAX_BYTES};

use super::{Connector, session};

pub(super) fn router(connector: Arc<Connector>) -> Router {
    Router::new()
        .route("/connector/v1", get(upgrade))
        .with_state(connector)
        .layer(middleware::from_fn(close_http))
}

async fn close_http(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;
    if response.status() != StatusCode::SWITCHING_PROTOCOLS {
        response
            .headers_mut()
            .insert("connection", "close".parse().expect("Static header"));
    }
    response
}

async fn upgrade(
    State(connector): State<Arc<Connector>>,
    method: Method,
    uri: Uri,
    headers: HeaderMap,
    upgrade: WebSocketUpgrade,
) -> Response {
    if method != Method::GET
        || uri.query().is_some()
        || !valid_origin(&headers)
        || headers.contains_key("sec-websocket-protocol")
    {
        return StatusCode::FORBIDDEN.into_response();
    }
    let Ok(pending) = Arc::clone(&connector.pending).try_acquire_owned() else {
        return StatusCode::SERVICE_UNAVAILABLE.into_response();
    };
    let Ok(connection) = Arc::clone(&connector.connections).try_acquire_owned() else {
        return StatusCode::SERVICE_UNAVAILABLE.into_response();
    };
    if connector
        .state
        .lock()
        .expect("Connector state lock poisoned")
        .stopping
    {
        return StatusCode::SERVICE_UNAVAILABLE.into_response();
    }
    upgrade
        .read_buffer_size(AUTHENTICATION_MAX_BYTES)
        .write_buffer_size(0)
        .max_write_buffer_size(CONTROL_MAX_BYTES + 1024)
        .max_frame_size(CONTROL_MAX_BYTES)
        .max_message_size(CONTROL_MAX_BYTES)
        .on_upgrade(move |socket| async move {
            let _connection = connection;
            session::run(socket, connector, pending).await;
        })
}

fn valid_origin(headers: &HeaderMap) -> bool {
    let mut origins = headers.get_all("origin").iter();
    let Some(origin) = origins.next().and_then(|value| value.to_str().ok()) else {
        return false;
    };
    if origins.next().is_some() {
        return false;
    }
    let Some(identifier) = origin.strip_prefix("moz-extension://") else {
        return false;
    };
    identifier.len() == 36
        && identifier.bytes().enumerate().all(|(index, character)| {
            if [8, 13, 18, 23].contains(&index) {
                character == b'-'
            } else {
                character.is_ascii_digit() || (b'a'..=b'f').contains(&character)
            }
        })
}

#[cfg(test)]
mod tests {
    use super::valid_origin;
    use axum::http::HeaderMap;

    #[test]
    fn origin_rejects_duplicates_and_noncanonical_values() {
        let valid = "moz-extension://12345678-1234-1234-1234-123456789abc";
        let mut headers = HeaderMap::new();
        headers.append("origin", valid.parse().unwrap());
        assert!(valid_origin(&headers));
        headers.append("origin", valid.parse().unwrap());
        assert!(!valid_origin(&headers));
        for invalid in [
            format!("{valid}/"),
            valid.to_uppercase(),
            format!("{valid}, {valid}"),
            "null".into(),
        ] {
            headers.clear();
            headers.insert("origin", invalid.parse().unwrap());
            assert!(!valid_origin(&headers));
        }
    }
}
