use std::io;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll};

use raicho_protocol::limits_generated::{MAXIMUM_AUTHENTICATION_BYTES, MAXIMUM_CONTROL_BYTES};
use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tokio::net::TcpStream;
use tokio::sync::OwnedSemaphorePermit;
use tokio_tungstenite::WebSocketStream;
use tokio_tungstenite::tungstenite::handshake::server::{Callback, ErrorResponse, Request, Response};
use tokio_tungstenite::tungstenite::http::{HeaderMap, StatusCode};
use tokio_tungstenite::tungstenite::protocol::WebSocketConfig;

use super::Connector;

const MAXIMUM_HEADER_BYTES: usize = 8192;

pub(super) type Socket = WebSocketStream<HandshakeLimit>;

pub(super) fn config() -> WebSocketConfig {
    WebSocketConfig::default()
        .read_buffer_size(MAXIMUM_AUTHENTICATION_BYTES)
        .write_buffer_size(0)
        .max_write_buffer_size(MAXIMUM_CONTROL_BYTES + 1024)
        .max_frame_size(Some(MAXIMUM_CONTROL_BYTES))
        .max_message_size(Some(MAXIMUM_CONTROL_BYTES))
}

pub(super) struct UpgradeCheck<'connection> {
    pub connector: &'connection Connector,
    pub pending: &'connection mut Option<OwnedSemaphorePermit>,
}

impl Callback for UpgradeCheck<'_> {
    fn on_request(self, request: &Request, response: Response) -> Result<Response, ErrorResponse> {
        match check(request, self.connector) {
            Ok(permit) => {
                *self.pending = Some(permit);
                Ok(response)
            }
            Err(status) => {
                let mut rejection = ErrorResponse::new(None);
                *rejection.status_mut() = status;
                Err(rejection)
            }
        }
    }
}

fn check(request: &Request, connector: &Connector) -> Result<OwnedSemaphorePermit, StatusCode> {
    if request.uri().path() != "/connector/v1" {
        return Err(StatusCode::NOT_FOUND);
    }
    if request.uri().query().is_some()
        || !valid_origin(request.headers())
        || request.headers().contains_key("sec-websocket-protocol")
    {
        return Err(StatusCode::FORBIDDEN);
    }
    if *connector.shutdown.borrow() {
        return Err(StatusCode::SERVICE_UNAVAILABLE);
    }
    Arc::clone(&connector.pending)
        .try_acquire_owned()
        .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)
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

pub(super) struct HandshakeLimit {
    stream: TcpStream,
    remaining: Option<usize>,
}

impl HandshakeLimit {
    pub(super) fn new(stream: TcpStream) -> Self {
        Self {
            stream,
            remaining: Some(MAXIMUM_HEADER_BYTES),
        }
    }

    pub(super) fn release(&mut self) {
        self.remaining = None;
    }
}

impl AsyncRead for HandshakeLimit {
    fn poll_read(self: Pin<&mut Self>, context: &mut Context<'_>, buffer: &mut ReadBuf<'_>) -> Poll<io::Result<()>> {
        let limited = self.get_mut();
        let previous = buffer.filled().len();
        let result = Pin::new(&mut limited.stream).poll_read(context, buffer);
        if let (Some(remaining), Poll::Ready(Ok(()))) = (limited.remaining.as_mut(), &result) {
            let read = buffer.filled().len() - previous;
            if read > *remaining {
                return Poll::Ready(Err(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "Connector upgrade headers too large",
                )));
            }
            *remaining -= read;
        }
        result
    }
}

impl AsyncWrite for HandshakeLimit {
    fn poll_write(self: Pin<&mut Self>, context: &mut Context<'_>, bytes: &[u8]) -> Poll<io::Result<usize>> {
        Pin::new(&mut self.get_mut().stream).poll_write(context, bytes)
    }

    fn poll_flush(self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().stream).poll_flush(context)
    }

    fn poll_shutdown(self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().stream).poll_shutdown(context)
    }
}
