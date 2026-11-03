use serde::Serialize;

// Mail values hold mail data, so they omit Debug and never reach logs.
#[derive(Clone, Serialize)]
pub struct Account {
    pub id: String,
    pub name: String,
    pub identities: Vec<Identity>,
}

#[derive(Clone, Serialize)]
pub struct Identity {
    pub id: String,
    pub name: String,
    pub email: String,
}

#[derive(Clone, Serialize)]
pub struct Mailboxes {
    pub mailboxes: Vec<Mailbox>,
    pub truncated: bool,
}

#[derive(Clone, Serialize)]
pub struct Mailbox {
    pub id: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub role: Option<MailboxRole>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailboxRole {
    Inbox,
    Drafts,
    Sent,
    Trash,
    Archive,
    Junk,
    Templates,
    Outbox,
}

/// One page of summaries and the backend cursor for the next page, if any.
#[derive(Clone)]
pub struct MessagePage {
    pub messages: Vec<MessageSummary>,
    pub cursor: Option<String>,
}

#[derive(Clone, Serialize)]
pub struct MessageSummary {
    pub id: String,
    pub subject: String,
    pub author: String,
    pub recipients: String,
    pub date: String,
    pub read: bool,
    pub flagged: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailFailure {
    InvalidRequest,
    BackendDisconnected,
    BackendBusy,
    BackendTimeout,
    StaleHandle,
    StaleCursor,
    Unsupported,
    BackendFailed,
}
