use super::{Account, MailBackend, MailFailure, Mailboxes, MessagePage};

/// Answers every mail request as unsupported, so no request frame reaches the connector.
///
/// The production extension answers mail requests only once the Thunderbird adapter ships
/// in stage 3 slice 5, and it treats any other frame as a protocol error that ends its session.
/// shortcut: the server uses this until that slice wires in `ConnectorBackend`.
pub struct UnsupportedBackend;

impl MailBackend for UnsupportedBackend {
    async fn accounts(&self) -> Result<Vec<Account>, MailFailure> {
        Err(MailFailure::Unsupported)
    }

    async fn mailboxes(&self, _account: &str) -> Result<Mailboxes, MailFailure> {
        Err(MailFailure::Unsupported)
    }

    async fn messages(&self, _mailbox: &str) -> Result<MessagePage, MailFailure> {
        Err(MailFailure::Unsupported)
    }

    async fn continue_messages(&self, _cursor: &str) -> Result<MessagePage, MailFailure> {
        Err(MailFailure::Unsupported)
    }

    async fn close(&self, _cursor: &str) {}
}

#[cfg(test)]
mod tests {
    use super::UnsupportedBackend;
    use crate::mail::{MailBackend, MailFailure};

    #[tokio::test]
    async fn every_request_is_unsupported() {
        let backend = UnsupportedBackend;
        assert!(matches!(backend.accounts().await, Err(MailFailure::Unsupported)));
        assert!(matches!(
            backend.mailboxes("account").await,
            Err(MailFailure::Unsupported)
        ));
        assert!(matches!(
            backend.messages("mailbox").await,
            Err(MailFailure::Unsupported)
        ));
        assert!(matches!(
            backend.continue_messages("cursor").await,
            Err(MailFailure::Unsupported)
        ));
    }
}
