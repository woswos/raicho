use std::ffi::OsStr;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::os::unix::ffi::OsStrExt;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

use rustix::process::{Pid, Signal, kill_process};
use tempfile::{TempDir, tempdir};

const DEADLINE: Duration = Duration::from_secs(20);

struct Deployment {
    directory: TempDir,
    bind: String,
    connector_bind: String,
}

impl Deployment {
    fn new() -> Self {
        let directory = tempdir().unwrap();
        std::fs::create_dir(directory.path().join("data")).unwrap();
        std::fs::create_dir(directory.path().join("web")).unwrap();
        std::fs::write(directory.path().join("web/index.html"), "Raicho").unwrap();
        Self {
            directory,
            bind: free_address(),
            connector_bind: free_address(),
        }
    }

    fn command(&self) -> Command {
        let mut command = Command::new(env!("CARGO_BIN_EXE_raicho-server"));
        command
            .env("RAICHO_BIND", &self.bind)
            .env("RAICHO_CONNECTOR_BIND", &self.connector_bind)
            .env("RAICHO_DATA_DIR", self.directory.path().join("data"))
            .env("RAICHO_WEB_DIR", self.directory.path().join("web"));
        command
    }

    fn failure(&self, command: &mut Command) -> String {
        let output = command.output().unwrap();
        assert!(!output.status.success(), "{output:?}");
        String::from_utf8(output.stderr).unwrap()
    }
}

fn free_address() -> String {
    TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
        .to_string()
}

struct Running(Child);

impl Drop for Running {
    fn drop(&mut self) {
        if let Ok(None) = self.0.try_wait() {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
}

fn start(deployment: &Deployment) -> Running {
    let mut child = deployment
        .command()
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let stderr = child.stderr.take().unwrap();
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        for line in BufReader::new(stderr).lines() {
            let _ = sender.send(line.unwrap());
        }
    });
    let running = Running(child);
    assert_eq!(
        receiver.recv_timeout(DEADLINE).unwrap(),
        "Raicho server ready"
    );
    running
}

fn live(address: &str) -> String {
    let mut stream = TcpStream::connect(address).unwrap();
    stream
        .write_all(b"GET /health/live HTTP/1.1\r\nHost: raicho\r\nConnection: close\r\n\r\n")
        .unwrap();
    let mut response = String::new();
    stream.read_to_string(&mut response).unwrap();
    response
}

fn wait(child: &mut Child) -> std::process::ExitStatus {
    let started = Instant::now();
    loop {
        if let Some(status) = child.try_wait().unwrap() {
            return status;
        }
        assert!(started.elapsed() < DEADLINE, "the server did not stop");
        thread::sleep(Duration::from_millis(50));
    }
}

#[test]
fn termination_and_interrupt_signals_stop_the_server_cleanly() {
    for signal in [Signal::TERM, Signal::INT] {
        let deployment = Deployment::new();
        let mut running = start(&deployment);
        let response = live(&deployment.bind);
        assert!(response.starts_with("HTTP/1.1 200 OK"), "{response}");
        assert!(response.contains("alive"), "{response}");
        let pid = Pid::from_raw(i32::try_from(running.0.id()).unwrap()).unwrap();
        kill_process(pid, signal).unwrap();
        assert!(wait(&mut running.0).success(), "{signal:?}");
    }
}

#[test]
fn startup_failures_exit_with_a_diagnostic() {
    let deployment = Deployment::new();
    std::fs::remove_file(deployment.directory.path().join("web/index.html")).unwrap();
    assert!(
        deployment
            .failure(&mut deployment.command())
            .contains("RAICHO_WEB_DIR must contain index.html")
    );
    let deployment = Deployment::new();
    for (name, value, message) in [
        (
            "RAICHO_BIND",
            OsStr::new("invalid"),
            "RAICHO_BIND must be an IP address and port",
        ),
        (
            "RAICHO_BIND",
            OsStr::from_bytes(b"\xff"),
            "RAICHO_BIND must contain valid Unicode",
        ),
        (
            "RAICHO_CONNECTOR_BIND",
            OsStr::from_bytes(b"\xff"),
            "RAICHO_CONNECTOR_BIND must contain valid Unicode",
        ),
    ] {
        let error = deployment.failure(deployment.command().env(name, value));
        assert!(error.starts_with("FAIL:"), "{error}");
        assert!(error.contains(message), "{error}");
    }
    for (occupied, message) in [
        (&deployment.bind, "Cannot bind HTTP listener"),
        (&deployment.connector_bind, "Cannot bind connector listener"),
    ] {
        let _holder = TcpListener::bind(occupied.as_str()).unwrap();
        let error = deployment.failure(&mut deployment.command());
        assert!(error.contains(message), "{error}");
    }
}
