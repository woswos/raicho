use std::sync::Arc;

use raicho_protocol::contract_generated::{
    self as wire, CloseList, CloseListName, ContinueList, ContinueListName, Generation, Handle, ListAccounts,
    ListAccountsName, ListMailboxes, ListMailboxesName, ListMessages, ListMessagesName, MailError, Operation, Outcome,
};

use super::MailBackend;
use super::contract::{Account, Identity, MailFailure, Mailbox, MailboxRole, Mailboxes, MessagePage, MessageSummary};
use crate::connector::{Connector, RequestFailure};

// The browser receives at most this many mailboxes per account, and the rest are reported as truncated.
pub const MAXIMUM_MAILBOXES: usize = 1000;

/// Forwards mail operations to the authenticated connector.
///
/// Every handle the browser receives is prefixed with the connection generation, so a
/// reconnect makes it stale before any request reaches Thunderbird.
pub struct ConnectorBackend {
    connector: Arc<Connector>,
}

impl ConnectorBackend {
    pub fn new(connector: Arc<Connector>) -> Self {
        Self { connector }
    }

    async fn request(
        &self,
        generation: Option<&Generation>,
        operation: Operation,
    ) -> Result<(Generation, Outcome), MailFailure> {
        let (generation, outcome) = self
            .connector
            .request(generation, operation)
            .await
            .map_err(request_failure)?;
        match outcome {
            Outcome::FailedResult(failed) => Err(mail_failure(failed.code)),
            outcome => Ok((generation, outcome)),
        }
    }

    async fn page(&self, generation: &Generation, operation: Operation) -> Result<MessagePage, MailFailure> {
        match self.request(Some(generation), operation).await {
            Ok((generation, Outcome::MessagesResult(result))) => Ok(MessagePage {
                messages: result
                    .messages
                    .into_iter()
                    .map(|summary| message_summary(&generation, summary))
                    .collect(),
                cursor: result.cursor.map(|cursor| scoped(&generation, &cursor)),
            }),
            Ok(_) => Err(MailFailure::BackendFailed),
            Err(failure) => Err(failure),
        }
    }
}

impl MailBackend for ConnectorBackend {
    async fn accounts(&self) -> Result<Vec<Account>, MailFailure> {
        let operation = Operation::ListAccounts(ListAccounts {
            name: ListAccountsName::ListAccounts,
        });
        let (generation, Outcome::AccountsResult(result)) = self.request(None, operation).await? else {
            return Err(MailFailure::BackendFailed);
        };
        Ok(result
            .accounts
            .into_iter()
            .map(|account| Account {
                id: scoped(&generation, &account.id),
                name: account.name.to_string(),
                identities: account
                    .identities
                    .into_iter()
                    .map(|identity| Identity {
                        id: scoped(&generation, &identity.id),
                        name: identity.name.to_string(),
                        email: identity.email.to_string(),
                    })
                    .collect(),
            })
            .collect())
    }

    async fn mailboxes(&self, account: &str) -> Result<Mailboxes, MailFailure> {
        let (generation, account) = unscoped(account)?;
        let mut operation = Operation::ListMailboxes(ListMailboxes {
            account,
            name: ListMailboxesName::ListMailboxes,
        });
        let mut mailboxes = Vec::new();
        loop {
            let (_, Outcome::MailboxesResult(result)) = self.request(Some(&generation), operation).await? else {
                return Err(MailFailure::BackendFailed);
            };
            mailboxes.extend(result.mailboxes.into_iter().map(|mailbox| Mailbox {
                id: scoped(&generation, &mailbox.id),
                name: mailbox.name.to_string(),
                parent: mailbox.parent.map(|parent| scoped(&generation, &parent)),
                role: mailbox.role.map(mailbox_role),
            }));
            let Some(cursor) = result.cursor else {
                return Ok(Mailboxes {
                    mailboxes,
                    truncated: false,
                });
            };
            if mailboxes.len() >= MAXIMUM_MAILBOXES {
                mailboxes.truncate(MAXIMUM_MAILBOXES);
                self.close(&scoped(&generation, &cursor)).await;
                return Ok(Mailboxes {
                    mailboxes,
                    truncated: true,
                });
            }
            operation = Operation::ContinueList(ContinueList {
                cursor,
                name: ContinueListName::ContinueList,
            });
        }
    }

    async fn messages(&self, mailbox: &str) -> Result<MessagePage, MailFailure> {
        let (generation, mailbox) = unscoped(mailbox)?;
        self.page(
            &generation,
            Operation::ListMessages(ListMessages {
                mailbox,
                name: ListMessagesName::ListMessages,
            }),
        )
        .await
    }

    async fn continue_messages(&self, cursor: &str) -> Result<MessagePage, MailFailure> {
        let (generation, cursor) = unscoped(cursor)?;
        self.page(
            &generation,
            Operation::ContinueList(ContinueList {
                cursor,
                name: ContinueListName::ContinueList,
            }),
        )
        .await
        .map_err(|failure| match failure {
            MailFailure::StaleHandle => MailFailure::StaleCursor,
            failure => failure,
        })
    }

    async fn close(&self, cursor: &str) {
        if let Ok((generation, cursor)) = unscoped(cursor) {
            let operation = Operation::CloseList(CloseList {
                cursor,
                name: CloseListName::CloseList,
            });
            let _ = self.request(Some(&generation), operation).await;
        }
    }
}

fn scoped(generation: &Generation, handle: &Handle) -> String {
    format!("{}.{}", generation.as_str(), handle.as_str())
}

fn unscoped(value: &str) -> Result<(Generation, Handle), MailFailure> {
    let (generation, handle) = value.split_once('.').ok_or(MailFailure::InvalidRequest)?;
    let generation = generation.parse().map_err(|_| MailFailure::InvalidRequest)?;
    let handle = handle.parse().map_err(|_| MailFailure::InvalidRequest)?;
    Ok((generation, handle))
}

fn request_failure(failure: RequestFailure) -> MailFailure {
    match failure {
        RequestFailure::Disconnected => MailFailure::BackendDisconnected,
        RequestFailure::StaleGeneration => MailFailure::StaleHandle,
        RequestFailure::Busy => MailFailure::BackendBusy,
        RequestFailure::Timeout => MailFailure::BackendTimeout,
    }
}

fn mail_failure(code: MailError) -> MailFailure {
    match code {
        MailError::StaleHandle => MailFailure::StaleHandle,
        MailError::StaleCursor => MailFailure::StaleCursor,
        MailError::Unsupported => MailFailure::Unsupported,
        MailError::Busy => MailFailure::BackendBusy,
        MailError::InvalidRequest | MailError::TooLarge | MailError::Failed => MailFailure::BackendFailed,
    }
}

fn mailbox_role(role: wire::MailboxRole) -> MailboxRole {
    match role {
        wire::MailboxRole::Inbox => MailboxRole::Inbox,
        wire::MailboxRole::Drafts => MailboxRole::Drafts,
        wire::MailboxRole::Sent => MailboxRole::Sent,
        wire::MailboxRole::Trash => MailboxRole::Trash,
        wire::MailboxRole::Archive => MailboxRole::Archive,
        wire::MailboxRole::Junk => MailboxRole::Junk,
        wire::MailboxRole::Templates => MailboxRole::Templates,
        wire::MailboxRole::Outbox => MailboxRole::Outbox,
    }
}

fn message_summary(generation: &Generation, summary: wire::MessageSummary) -> MessageSummary {
    MessageSummary {
        id: scoped(generation, &summary.id),
        subject: summary.subject.to_string(),
        author: summary.author.to_string(),
        recipients: summary.recipients.to_string(),
        date: summary.date.to_string(),
        read: summary.read,
        flagged: summary.flagged,
    }
}
