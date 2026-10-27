use std::io;
use std::pin::Pin;
use std::task::{Context, Poll};

use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tokio::net::TcpStream;

const MAXIMUM_HEADER_BYTES: usize = 8192;

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
                    "Connector upgrade headers exceed the limit",
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
