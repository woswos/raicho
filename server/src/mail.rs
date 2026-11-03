mod connector_backend;
mod contract;

use std::future::Future;

pub use connector_backend::ConnectorBackend;
pub use contract::{Account, Identity, MailFailure, Mailbox, MailboxRole, Mailboxes, MessagePage, MessageSummary};

/// A mail backend that browser routes use without knowing its implementation.
///
/// Handles and cursors are opaque strings that the backend issues and validates.
pub trait MailBackend: Send + Sync + 'static {
    fn accounts(&self) -> impl Future<Output = Result<Vec<Account>, MailFailure>> + Send;

    fn mailboxes(&self, account: &str) -> impl Future<Output = Result<Mailboxes, MailFailure>> + Send;

    fn messages(&self, mailbox: &str) -> impl Future<Output = Result<MessagePage, MailFailure>> + Send;

    fn continue_messages(&self, cursor: &str) -> impl Future<Output = Result<MessagePage, MailFailure>> + Send;

    fn close(&self, cursor: &str) -> impl Future<Output = ()> + Send;
}
