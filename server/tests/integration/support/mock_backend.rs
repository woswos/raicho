use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};

use raicho_server::mail::{
    Account, Identity, MailBackend, MailFailure, Mailbox, MailboxRole, Mailboxes, MessagePage, MessageSummary,
};

pub const ACCOUNT: &str = "mock.account";
pub const INBOX: &str = "mock.inbox";
pub const SECOND_PAGE: &str = "mock.page-2";
pub const SUBJECT: &str = "Fictional summary Grüße";

/// A fictional backend that stands in for Thunderbird behind the same routes.
#[derive(Default)]
pub struct MockBackend {
    pub disconnected: AtomicBool,
    pub closed: Mutex<Vec<String>>,
}

fn summary(identifier: &str) -> MessageSummary {
    MessageSummary {
        id: identifier.into(),
        subject: SUBJECT.into(),
        author: "Zoë <zoe@raicho.test>".into(),
        recipients: "sender@raicho.test".into(),
        date: "2026-11-03T08:00:00Z".into(),
        read: false,
        flagged: true,
    }
}

impl MockBackend {
    fn available(&self) -> Result<(), MailFailure> {
        if self.disconnected.load(Ordering::SeqCst) {
            Err(MailFailure::BackendDisconnected)
        } else {
            Ok(())
        }
    }
}

impl MailBackend for MockBackend {
    async fn accounts(&self) -> Result<Vec<Account>, MailFailure> {
        self.available()?;
        Ok(vec![Account {
            id: ACCOUNT.into(),
            name: "Fictional account".into(),
            identities: vec![Identity {
                id: "mock.identity".into(),
                name: "Zoë".into(),
                email: "zoe@raicho.test".into(),
            }],
        }])
    }

    async fn mailboxes(&self, account: &str) -> Result<Mailboxes, MailFailure> {
        self.available()?;
        if account != ACCOUNT {
            return Err(MailFailure::StaleHandle);
        }
        Ok(Mailboxes {
            mailboxes: vec![
                Mailbox {
                    id: INBOX.into(),
                    name: "Inbox".into(),
                    parent: None,
                    role: Some(MailboxRole::Inbox),
                },
                Mailbox {
                    id: "mock.projects".into(),
                    name: "Projekte".into(),
                    parent: Some(INBOX.into()),
                    role: None,
                },
            ],
            truncated: false,
        })
    }

    async fn messages(&self, mailbox: &str) -> Result<MessagePage, MailFailure> {
        self.available()?;
        if mailbox != INBOX {
            return Err(MailFailure::StaleHandle);
        }
        Ok(MessagePage {
            messages: vec![summary("mock.message-1"), summary("mock.message-2")],
            cursor: Some(SECOND_PAGE.into()),
        })
    }

    async fn continue_messages(&self, cursor: &str) -> Result<MessagePage, MailFailure> {
        self.available()?;
        if cursor != SECOND_PAGE {
            return Err(MailFailure::StaleCursor);
        }
        Ok(MessagePage {
            messages: vec![summary("mock.message-3")],
            cursor: None,
        })
    }

    async fn close(&self, cursor: &str) {
        self.closed.lock().unwrap().push(cursor.into());
    }
}
