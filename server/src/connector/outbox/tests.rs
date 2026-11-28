use std::convert::Infallible;

use futures_util::sink;
use raicho_protocol::Phase;
use raicho_protocol::channel::{Channel, Peer};
use raicho_protocol::contract_generated::{ConnectorMessage, Generation};
use raicho_protocol::diagnostics_generated::BackendError;
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::Message;

use super::OUTBOX_FRAMES;
use crate::connector::failure::Failure;
use crate::connector::heartbeat::Heartbeat;
use crate::connector::wire;

#[tokio::test]
async fn a_frame_the_full_queue_rejects_leaves_the_terminal_counter_in_order() {
    let generation: Generation = "0123456789abcdef0123456789abcdef".parse().unwrap();
    let mut channel = Channel::new([7; 32], Peer::Server);
    let mut peer = Channel::new([7; 32], Peer::Client);
    let (written_sender, mut written) = mpsc::unbounded_channel();
    let writer = Box::pin(sink::unfold(written_sender, |sender, message: Message| async move {
        if let Message::Text(text) = message {
            let _ = sender.send(text.to_string());
        }
        Ok::<_, Infallible>(sender)
    }));
    let (outbox, outgoing) = super::channel(writer);
    for sequence in 1..=OUTBOX_FRAMES as u64 {
        assert!(outbox.reserve().is_ok_and(|slot| {
            slot.send(wire::ping(&generation, sequence, &mut channel));
            true
        }));
    }

    let failure = Heartbeat::new()
        .send_ping(&outbox, &generation, &mut channel)
        .err()
        .unwrap();
    assert_eq!(failure.diagnostic, BackendError::Disconnected);
    let (mut writer, queued) = outgoing.finish();
    let failure = Failure::new(BackendError::Disconnected);
    wire::terminate(&mut writer, Some((&generation, &mut channel)), queued, failure).await;

    let mut opened = Vec::new();
    while let Ok(frame) = written.try_recv() {
        opened.push(
            peer.open(&frame, Phase::ServerControl, &generation)
                .map(|message| match message {
                    ConnectorMessage::Ping(_) => "ping",
                    ConnectorMessage::ProtocolError(_) => "error",
                    _ => "other",
                }),
        );
    }
    assert_eq!(opened.len(), OUTBOX_FRAMES + 1);
    assert!(opened[..OUTBOX_FRAMES].iter().all(|frame| *frame == Ok("ping")));
    assert_eq!(opened[OUTBOX_FRAMES], Ok("error"));
}
