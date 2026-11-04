use axum::Json;
use axum::extract::{Path, State};
use axum::response::{IntoResponse, Response};
use serde::Serialize;

use super::ApplicationState;
use super::api_error::ApiError;
use super::guard::BrowserSession;
use crate::mail::{Account, MailBackend, MessagePage, MessageSummary};

#[derive(Serialize)]
pub struct AccountsDocument {
    accounts: Vec<Account>,
}

#[derive(Serialize)]
pub struct MessagesDocument {
    messages: Vec<MessageSummary>,
    #[serde(skip_serializing_if = "Option::is_none")]
    cursor: Option<String>,
}

// Backends issue opaque handles, so the route checks only their shape before passing them on.
fn handle(value: &str) -> Result<&str, ApiError> {
    if (1..=128).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        Ok(value)
    } else {
        Err(ApiError::InvalidRequest)
    }
}

pub async fn accounts<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    _session: BrowserSession,
) -> Result<Json<AccountsDocument>, ApiError> {
    Ok(Json(AccountsDocument {
        accounts: state.backend.accounts().await?,
    }))
}

pub async fn mailboxes<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    _session: BrowserSession,
    Path(account): Path<String>,
) -> Result<Response, ApiError> {
    Ok(Json(state.backend.mailboxes(handle(&account)?).await?).into_response())
}

pub async fn messages<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    BrowserSession(session): BrowserSession,
    Path(mailbox): Path<String>,
) -> Result<Json<MessagesDocument>, ApiError> {
    let page = state.backend.messages(handle(&mailbox)?).await?;
    document(&state, &session, page)
}

pub async fn next_page<Backend: MailBackend>(
    State(state): State<ApplicationState<Backend>>,
    BrowserSession(session): BrowserSession,
    Path(cursor): Path<String>,
) -> Result<Json<MessagesDocument>, ApiError> {
    let (backend_cursor, released) = state.cursors.take(&session, &cursor);
    state.close_cursors(released);
    let backend_cursor = backend_cursor.ok_or(ApiError::StaleCursor)?;
    let page = state.backend.continue_messages(&backend_cursor).await?;
    document(&state, &session, page)
}

fn document<Backend: MailBackend>(
    state: &ApplicationState<Backend>,
    session: &crate::persistence::TokenDigest,
    page: MessagePage,
) -> Result<Json<MessagesDocument>, ApiError> {
    let cursor = match page.cursor {
        Some(backend_cursor) => {
            let (cursor, released) = state
                .cursors
                .issue(session, backend_cursor)
                .ok_or(ApiError::BackendFailed)?;
            state.close_cursors(released);
            Some(cursor)
        }
        None => None,
    };
    Ok(Json(MessagesDocument {
        messages: page.messages,
        cursor,
    }))
}
