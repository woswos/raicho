use std::net::{Ipv4Addr, Ipv6Addr};

use crate::error::{Error, Result};

const LOOPBACK_HOSTS: [&str; 3] = ["localhost", "127.0.0.1", "[::1]"];

/// The one origin browsers use to reach this deployment, as their `Origin` header spells it.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PublicOrigin {
    serialized: String,
    secure: bool,
}

impl PublicOrigin {
    pub fn parse(value: &str) -> Result<Self> {
        let invalid = || Error::message("RAICHO_PUBLIC_ORIGIN must be an http or https origin without a path");
        let value = value.to_ascii_lowercase();
        let (secure, authority) = if let Some(authority) = value.strip_prefix("https://") {
            (true, authority)
        } else if let Some(authority) = value.strip_prefix("http://") {
            (false, authority)
        } else {
            return Err(invalid());
        };
        let (host, port) = match authority.rsplit_once(':') {
            Some((host, port)) if !port.contains(']') => (host, Some(port)),
            _ => (authority, None),
        };
        if !valid_host(host) || port.is_some_and(|port| !valid_port(port, secure)) {
            return Err(invalid());
        }
        if !secure && !LOOPBACK_HOSTS.contains(&host) {
            return Err(Error::message(
                "RAICHO_PUBLIC_ORIGIN must use https unless its host is loopback",
            ));
        }
        Ok(Self {
            serialized: value,
            secure,
        })
    }

    pub fn as_str(&self) -> &str {
        &self.serialized
    }

    pub fn is_secure(&self) -> bool {
        self.secure
    }

    // Some browsers reject `__Host-` and `Secure` cookies on plain loopback HTTP.
    pub fn cookie_name(&self) -> &'static str {
        if self.secure {
            "__Host-raicho_session"
        } else {
            "raicho_session"
        }
    }
}

fn valid_host(host: &str) -> bool {
    if let Some(address) = host.strip_prefix('[').and_then(|rest| rest.strip_suffix(']')) {
        return address
            .parse::<Ipv6Addr>()
            .is_ok_and(|parsed| browser_form(parsed) == address);
    }
    // Browsers parse a host ending in a numeric label as IPv4 and send its dotted decimal form.
    let last_label = host.rsplit('.').next().unwrap_or_default();
    if last_label.bytes().all(|byte| byte.is_ascii_digit()) || last_label.starts_with("0x") {
        return host
            .parse::<Ipv4Addr>()
            .is_ok_and(|address| address.to_string() == host);
    }
    !host.is_empty()
        && host.len() <= 253
        && host.split('.').all(|label| {
            !label.is_empty()
                && label.len() <= 63
                && !label.starts_with('-')
                && !label.ends_with('-')
                && label.bytes().all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
        })
}

/// The IPv6 form a browser's `Origin` header uses: lowercase hexadecimal pieces with the first
/// longest run of two or more zero pieces compressed. Unlike `Ipv6Addr`'s `Display`, it never
/// writes an IPv4-mapped tail in dotted form.
fn browser_form(address: Ipv6Addr) -> String {
    let pieces = address.segments();
    let (mut run_start, mut run_length) = (0, 0);
    let mut index = 0;
    while index < pieces.len() {
        let start = index;
        while index < pieces.len() && pieces[index] == 0 {
            index += 1;
        }
        if index - start > run_length {
            (run_start, run_length) = (start, index - start);
        }
        index = index.max(start + 1);
    }
    let join = |pieces: &[u16]| {
        pieces
            .iter()
            .map(|piece| format!("{piece:x}"))
            .collect::<Vec<_>>()
            .join(":")
    };
    if run_length < 2 {
        return join(&pieces);
    }
    format!(
        "{}::{}",
        join(&pieces[..run_start]),
        join(&pieces[run_start + run_length..])
    )
}

// Browsers omit a scheme's default port from Origin, so a configured default port would never match.
fn valid_port(port: &str, secure: bool) -> bool {
    !port.starts_with('0')
        && port.bytes().all(|byte| byte.is_ascii_digit())
        && port
            .parse::<u16>()
            .is_ok_and(|port| port != if secure { 443 } else { 80 })
}

#[cfg(test)]
mod tests {
    use super::PublicOrigin;

    #[test]
    fn https_origins_and_loopback_http_are_accepted() {
        for (value, secure) in [
            ("https://mail.example.org", true),
            ("https://MAIL.example.org:8443", true),
            ("http://localhost:8080", false),
            ("http://127.0.0.1:8080", false),
            ("http://[::1]:8080", false),
            ("https://192.168.1.2:8443", true),
            ("https://[2001:db8::1]:8443", true),
            ("https://[2001:DB8::1]", true),
            ("https://[::ffff:7f00:1]", true),
            ("https://[2001:db8::1:0:0:1]", true),
            ("https://[1:0:0:2::3]", true),
            ("https://[::]", true),
        ] {
            let origin = PublicOrigin::parse(value).unwrap();
            assert_eq!(origin.as_str(), value.to_ascii_lowercase());
            assert_eq!(origin.is_secure(), secure);
        }
        assert_eq!(
            PublicOrigin::parse("https://mail.example.org").unwrap().cookie_name(),
            "__Host-raicho_session"
        );
        assert_eq!(
            PublicOrigin::parse("http://localhost:8080").unwrap().cookie_name(),
            "raicho_session"
        );
    }

    #[test]
    fn plain_http_paths_default_ports_and_malformed_hosts_are_rejected() {
        for value in [
            "http://mail.example.org",
            "http://192.168.1.2:8080",
            "https://mail.example.org/",
            "https://mail.example.org:443",
            "http://localhost:80",
            "https://mail.example.org:0",
            "https://mail.example.org:65536",
            "https://-mail.example.org",
            "https://mail..example.org",
            "https://user@mail.example.org",
            "ftp://mail.example.org",
            "mail.example.org",
            "https://",
            "https://127.000.000.001",
            "https://0x7f.0.0.1",
            "https://2130706433",
            "http://127.1:8080",
            "https://mail.example.123",
            "http://[2001:db8::1]:8080",
            "https://[2001:db8:0:0:0:0:0:1]",
            "https://[::ffff:127.0.0.1]",
            "https://[2001:db8:0:0:1::1]",
            "https://[2001:db8::0001]",
            "https://[mail.example.org]",
            "https://[::1",
        ] {
            assert!(PublicOrigin::parse(value).is_err(), "{value}");
        }
    }
}
