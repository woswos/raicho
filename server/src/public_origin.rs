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
    host == "[::1]"
        || (!host.is_empty()
            && host.len() <= 253
            && host.split('.').all(|label| {
                !label.is_empty()
                    && label.len() <= 63
                    && !label.starts_with('-')
                    && !label.ends_with('-')
                    && label.bytes().all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
            }))
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
        ] {
            assert!(PublicOrigin::parse(value).is_err(), "{value}");
        }
    }
}
