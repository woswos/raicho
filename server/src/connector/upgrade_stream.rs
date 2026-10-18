use std::future::Future;
use std::io;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::Duration;

use raicho_protocol::limits_generated::AUTHENTICATION_DEADLINE_MS;
use tokio::io::{AsyncRead, AsyncWrite, ReadBuf};
use tokio::net::TcpStream;
use tokio::sync::OwnedSemaphorePermit;
use tokio::time::Sleep;

pub struct UpgradeStream {
    stream: TcpStream,
    _permit: OwnedSemaphorePermit,
    deadline: Pin<Box<Sleep>>,
    header_bytes: usize,
    header_suffix: u32,
    upgraded: bool,
}

impl UpgradeStream {
    pub(super) fn new(stream: TcpStream, permit: OwnedSemaphorePermit) -> Self {
        Self {
            stream,
            _permit: permit,
            deadline: Box::pin(tokio::time::sleep(Duration::from_millis(
                AUTHENTICATION_DEADLINE_MS as u64,
            ))),
            header_bytes: 0,
            header_suffix: 0,
            upgraded: false,
        }
    }
}

impl AsyncRead for UpgradeStream {
    fn poll_read(
        self: Pin<&mut Self>,
        context: &mut Context<'_>,
        buffer: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>> {
        let stream = self.get_mut();
        if !stream.upgraded && stream.deadline.as_mut().poll(context).is_ready() {
            return Poll::Ready(Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "Connector upgrade timed out",
            )));
        }
        let previous = buffer.filled().len();
        let result = Pin::new(&mut stream.stream).poll_read(context, buffer);
        if !stream.upgraded && matches!(result, Poll::Ready(Ok(()))) {
            for byte in &buffer.filled()[previous..] {
                stream.header_bytes += 1;
                if stream.header_bytes > 8192 {
                    return Poll::Ready(Err(io::Error::new(
                        io::ErrorKind::InvalidData,
                        "Connector upgrade headers too large",
                    )));
                }
                stream.header_suffix = (stream.header_suffix << 8) | u32::from(*byte);
                if stream.header_suffix == 0x0d0a0d0a {
                    stream.upgraded = true;
                    break;
                }
            }
        }
        result
    }
}

impl AsyncWrite for UpgradeStream {
    fn poll_write(
        self: Pin<&mut Self>,
        context: &mut Context<'_>,
        bytes: &[u8],
    ) -> Poll<io::Result<usize>> {
        Pin::new(&mut self.get_mut().stream).poll_write(context, bytes)
    }
    fn poll_flush(self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().stream).poll_flush(context)
    }
    fn poll_shutdown(self: Pin<&mut Self>, context: &mut Context<'_>) -> Poll<io::Result<()>> {
        Pin::new(&mut self.get_mut().stream).poll_shutdown(context)
    }
}
