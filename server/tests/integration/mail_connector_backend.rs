use std::sync::Arc;

use futures_util::SinkExt;
use raicho_protocol::Phase;
use raicho_protocol::channel::Channel;
use raicho_server::mail::{ConnectorBackend, MailBackend, MailFailure};
use serde_json::{Value, json};
use tokio_tungstenite::tungstenite::Message;

use crate::support::{Fixture, Socket, receive};

struct Connection {
    socket: Socket,
    channel: Channel,
    generation: String,
}

impl Connection {
    async fn open(fixture: &Fixture) -> Self {
        let (socket, welcome, channel) = fixture.session().await;
        Self {
            socket,
            channel,
            generation: welcome["generation"].as_str().unwrap().to_owned(),
        }
    }

    async fn answer(&mut self, result: Value) -> Value {
        let request = receive(&mut self.socket).await;
        self.channel
            .open(&request.to_string(), Phase::ServerControl, &self.generation)
            .unwrap();
        let reply = json!({"type":"reply","protocol_version":2,"generation":self.generation,
            "request_id":request["request_id"],"result":result});
        self.socket
            .send(Message::Text(self.channel.seal(&reply).into()))
            .await
            .unwrap();
        request["operation"].clone()
    }
}

fn handle(character: char) -> String {
    character.to_string().repeat(22)
}

#[tokio::test]
async fn handles_carry_the_generation_and_mailbox_pages_are_joined() {
    let fixture = Fixture::new().await;
    let backend = Arc::new(ConnectorBackend::new(Arc::clone(&fixture.connector)));
    let mut connection = Connection::open(&fixture).await;
    let generation = connection.generation.clone();

    let accounts = tokio::spawn({
        let backend = Arc::clone(&backend);
        async move { backend.accounts().await }
    });
    connection
        .answer(json!({"kind":"accounts","accounts":[{"id":handle('A'),"name":"Arbeit",
            "identities":[{"id":handle('I'),"name":"Zoë","email":"zoe@raicho.test"}]}]}))
        .await;
    let accounts = accounts.await.unwrap().ok().unwrap();
    let account = accounts[0].id.clone();
    assert_eq!(account, format!("{generation}.{}", handle('A')));
    assert_eq!(accounts[0].identities[0].id, format!("{generation}.{}", handle('I')));

    let mailboxes = tokio::spawn({
        let backend = Arc::clone(&backend);
        let account = account.clone();
        async move { backend.mailboxes(&account).await }
    });
    let first = connection
        .answer(
            json!({"kind":"mailboxes","mailboxes":[{"id":handle('B'),"name":"Inbox","role":"inbox"}],
            "cursor":handle('C')}),
        )
        .await;
    assert_eq!(first, json!({"name":"list_mailboxes","account":handle('A')}));
    let second = connection
        .answer(json!({"kind":"mailboxes","mailboxes":[{"id":handle('D'),"name":"Projekte","parent":handle('B')}]}))
        .await;
    assert_eq!(second, json!({"name":"continue_list","cursor":handle('C')}));
    let mailboxes = mailboxes.await.unwrap().ok().unwrap();
    assert!(!mailboxes.truncated);
    assert_eq!(mailboxes.mailboxes.len(), 2);
    assert_eq!(
        mailboxes.mailboxes[1].parent,
        Some(format!("{generation}.{}", handle('B')))
    );

    let page = tokio::spawn({
        let backend = Arc::clone(&backend);
        let mailbox = mailboxes.mailboxes[0].id.clone();
        async move { backend.messages(&mailbox).await }
    });
    connection
        .answer(
            json!({"kind":"messages","messages":[{"id":handle('M'),"subject":"Grüße","author":"Zoë",
            "recipients":"","date":"2026-11-03T08:00:00Z","read":false,"flagged":true}],"cursor":handle('E')}),
        )
        .await;
    let page = page.await.unwrap().ok().unwrap();
    assert_eq!(page.messages[0].subject, "Grüße");
    assert_eq!(page.cursor, Some(format!("{generation}.{}", handle('E'))));
    fixture.finish().await;
}

#[tokio::test]
async fn handles_from_a_previous_connection_are_stale_without_a_request() {
    let fixture = Fixture::new().await;
    let backend = ConnectorBackend::new(Arc::clone(&fixture.connector));
    let first = Connection::open(&fixture).await;
    let account = format!("{}.{}", first.generation, handle('A'));
    let cursor = format!("{}.{}", first.generation, handle('C'));
    let _replacement = Connection::open(&fixture).await;
    assert_eq!(backend.mailboxes(&account).await.err(), Some(MailFailure::StaleHandle));
    assert_eq!(backend.messages(&account).await.err(), Some(MailFailure::StaleHandle));
    assert_eq!(
        backend.continue_messages(&cursor).await.err(),
        Some(MailFailure::StaleCursor)
    );
    for malformed in [
        "",
        "no-separator",
        "zz.AAAAAAAAAAAAAAAAAAAAAA",
        &format!("{}.short", first.generation),
    ] {
        assert_eq!(
            backend.mailboxes(malformed).await.err(),
            Some(MailFailure::InvalidRequest)
        );
    }
    fixture.finish().await;
}

#[tokio::test]
async fn connector_failures_keep_their_category() {
    let fixture = Fixture::new().await;
    let backend = Arc::new(ConnectorBackend::new(Arc::clone(&fixture.connector)));
    let mut connection = Connection::open(&fixture).await;
    let mailbox = format!("{}.{}", connection.generation, handle('B'));
    for (code, expected) in [
        ("stale_handle", MailFailure::StaleHandle),
        ("unsupported", MailFailure::Unsupported),
        ("busy", MailFailure::BackendBusy),
        ("too_large", MailFailure::BackendFailed),
    ] {
        let page = tokio::spawn({
            let backend = Arc::clone(&backend);
            let mailbox = mailbox.clone();
            async move { backend.messages(&mailbox).await }
        });
        connection.answer(json!({"kind":"error","code":code})).await;
        assert_eq!(page.await.unwrap().err(), Some(expected));
    }
    let wrong_kind = tokio::spawn({
        let backend = Arc::clone(&backend);
        async move { backend.accounts().await }
    });
    connection.answer(json!({"kind":"closed"})).await;
    assert_eq!(wrong_kind.await.unwrap().err(), Some(MailFailure::BackendFailed));
    drop(connection);
    assert_eq!(backend.accounts().await.err(), Some(MailFailure::BackendDisconnected));
    fixture.finish().await;
}

#[tokio::test]
async fn mailbox_pages_stop_at_the_limit_and_close_the_list() {
    let fixture = Fixture::new().await;
    let backend = Arc::new(ConnectorBackend::new(Arc::clone(&fixture.connector)));
    let mut connection = Connection::open(&fixture).await;
    let account = format!("{}.{}", connection.generation, handle('A'));
    let roles = [
        "inbox",
        "drafts",
        "sent",
        "trash",
        "archive",
        "junk",
        "templates",
        "outbox",
    ];
    let page = |offset: usize| {
        let mailboxes: Vec<Value> = (offset..offset + 400)
            .map(|index| {
                let mut mailbox = json!({"id": format!("{index:022}"), "name": format!("Folder {index}")});
                if let Some(role) = roles.get(index) {
                    mailbox["role"] = json!(role);
                }
                mailbox
            })
            .collect();
        json!({"kind":"mailboxes","mailboxes":mailboxes,"cursor":handle('C')})
    };
    let mailboxes = tokio::spawn({
        let backend = Arc::clone(&backend);
        async move { backend.mailboxes(&account).await }
    });
    for offset in [0, 400, 800] {
        connection.answer(page(offset)).await;
    }
    assert_eq!(
        connection.answer(json!({"kind":"closed"})).await,
        json!({"name":"close_list","cursor":handle('C')})
    );
    let mailboxes = mailboxes.await.unwrap().ok().unwrap();
    assert!(mailboxes.truncated);
    assert_eq!(mailboxes.mailboxes.len(), 1000);
    let mapped: Vec<_> = mailboxes.mailboxes[..8].iter().map(|mailbox| mailbox.role).collect();
    assert_eq!(serde_json::to_value(mapped).unwrap(), json!(roles));
    fixture.finish().await;
}

#[tokio::test]
async fn results_of_the_wrong_kind_fail_and_remaining_codes_map_to_failures() {
    let fixture = Fixture::new().await;
    let backend = Arc::new(ConnectorBackend::new(Arc::clone(&fixture.connector)));
    let mut connection = Connection::open(&fixture).await;
    let generation = connection.generation.clone();
    let mailbox = format!("{generation}.{}", handle('B'));
    let cursor = format!("{generation}.{}", handle('C'));
    let accounts = json!({"kind":"accounts","accounts":[]});
    for (operation, result, expected) in [
        ("messages", accounts.clone(), MailFailure::BackendFailed),
        ("mailboxes", accounts.clone(), MailFailure::BackendFailed),
        (
            "next",
            json!({"kind":"error","code":"stale_handle"}),
            MailFailure::StaleCursor,
        ),
        (
            "next",
            json!({"kind":"error","code":"stale_cursor"}),
            MailFailure::StaleCursor,
        ),
        (
            "messages",
            json!({"kind":"error","code":"invalid_request"}),
            MailFailure::BackendFailed,
        ),
        (
            "messages",
            json!({"kind":"error","code":"failed"}),
            MailFailure::BackendFailed,
        ),
    ] {
        let request = tokio::spawn({
            let backend = Arc::clone(&backend);
            let (mailbox, cursor) = (mailbox.clone(), cursor.clone());
            async move {
                match operation {
                    "messages" => backend.messages(&mailbox).await.err(),
                    "mailboxes" => backend.mailboxes(&mailbox).await.err(),
                    _ => backend.continue_messages(&cursor).await.err(),
                }
            }
        });
        connection.answer(result).await;
        assert_eq!(request.await.unwrap(), Some(expected), "{operation}");
    }
    fixture.finish().await;
}
