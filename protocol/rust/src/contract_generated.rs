// Generated from protocol/schema/connector.schema.json.
///`Authenticate`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Authenticate {
    pub backend_kind: AuthenticateBackendKind,
    pub backend_version: AuthenticateBackendVersion,
    pub capabilities: Capabilities,
    pub client_nonce: Nonce,
    pub client_proof: Signature,
    pub connector_version: AuthenticateConnectorVersion,
    pub protocol_version: AuthenticateProtocolVersion,
    #[serde(rename = "type")]
    pub type_: AuthenticateType,
}
///`AuthenticateBackendKind`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct AuthenticateBackendKind(::std::string::String);
impl ::std::ops::Deref for AuthenticateBackendKind {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<AuthenticateBackendKind> for ::std::string::String {
    fn from(value: AuthenticateBackendKind) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for AuthenticateBackendKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 32usize {
            return Err("longer than 32 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[a-z][a-z0-9_]*$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[a-z][a-z0-9_]*$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for AuthenticateBackendKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AuthenticateBackendKind {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for AuthenticateBackendKind {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`AuthenticateBackendVersion`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct AuthenticateBackendVersion(::std::string::String);
impl ::std::ops::Deref for AuthenticateBackendVersion {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<AuthenticateBackendVersion> for ::std::string::String {
    fn from(value: AuthenticateBackendVersion) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for AuthenticateBackendVersion {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 64usize {
            return Err("longer than 64 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[ -~]+$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[ -~]+$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for AuthenticateBackendVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AuthenticateBackendVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for AuthenticateBackendVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`AuthenticateConnectorVersion`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct AuthenticateConnectorVersion(::std::string::String);
impl ::std::ops::Deref for AuthenticateConnectorVersion {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<AuthenticateConnectorVersion> for ::std::string::String {
    fn from(value: AuthenticateConnectorVersion) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for AuthenticateConnectorVersion {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 64usize {
            return Err("longer than 64 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[ -~]+$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[ -~]+$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for AuthenticateConnectorVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AuthenticateConnectorVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for AuthenticateConnectorVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`AuthenticateProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct AuthenticateProtocolVersion(i64);
impl ::std::ops::Deref for AuthenticateProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<AuthenticateProtocolVersion> for i64 {
    fn from(value: AuthenticateProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for AuthenticateProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for AuthenticateProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`AuthenticateType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum AuthenticateType {
    #[serde(rename = "authenticate")]
    Authenticate,
}
impl ::std::fmt::Display for AuthenticateType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Authenticate => f.write_str("authenticate"),
        }
    }
}
impl ::std::str::FromStr for AuthenticateType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "authenticate" => Ok(Self::Authenticate),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for AuthenticateType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AuthenticateType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`Capabilities`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct Capabilities(pub ::std::vec::Vec<::std::string::String>);
impl ::std::ops::Deref for Capabilities {
    type Target = ::std::vec::Vec<::std::string::String>;
    fn deref(&self) -> &::std::vec::Vec<::std::string::String> {
        &self.0
    }
}
impl ::std::convert::From<Capabilities> for ::std::vec::Vec<::std::string::String> {
    fn from(value: Capabilities) -> Self {
        value.0
    }
}
impl ::std::convert::From<::std::vec::Vec<::std::string::String>> for Capabilities {
    fn from(value: ::std::vec::Vec<::std::string::String>) -> Self {
        Self(value)
    }
}
///`Challenge`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Challenge {
    pub protocol_version: ChallengeProtocolVersion,
    pub server_nonce: Nonce,
    #[serde(rename = "type")]
    pub type_: ChallengeType,
}
///`ChallengeProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct ChallengeProtocolVersion(i64);
impl ::std::ops::Deref for ChallengeProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<ChallengeProtocolVersion> for i64 {
    fn from(value: ChallengeProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for ChallengeProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for ChallengeProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`ChallengeType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ChallengeType {
    #[serde(rename = "challenge")]
    Challenge,
}
impl ::std::fmt::Display for ChallengeType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Challenge => f.write_str("challenge"),
        }
    }
}
impl ::std::str::FromStr for ChallengeType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "challenge" => Ok(Self::Challenge),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ChallengeType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ChallengeType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ConnectorMessage`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(untagged)]
pub enum ConnectorMessage {
    Challenge(Challenge),
    Authenticate(Authenticate),
    Welcome(Welcome),
    Ping(Ping),
    Pong(Pong),
    ProtocolError(ProtocolError),
}
impl ::std::convert::From<Challenge> for ConnectorMessage {
    fn from(value: Challenge) -> Self {
        Self::Challenge(value)
    }
}
impl ::std::convert::From<Authenticate> for ConnectorMessage {
    fn from(value: Authenticate) -> Self {
        Self::Authenticate(value)
    }
}
impl ::std::convert::From<Welcome> for ConnectorMessage {
    fn from(value: Welcome) -> Self {
        Self::Welcome(value)
    }
}
impl ::std::convert::From<Ping> for ConnectorMessage {
    fn from(value: Ping) -> Self {
        Self::Ping(value)
    }
}
impl ::std::convert::From<Pong> for ConnectorMessage {
    fn from(value: Pong) -> Self {
        Self::Pong(value)
    }
}
impl ::std::convert::From<ProtocolError> for ConnectorMessage {
    fn from(value: ProtocolError) -> Self {
        Self::ProtocolError(value)
    }
}
///`Generation`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct Generation(::std::string::String);
impl ::std::ops::Deref for Generation {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<Generation> for ::std::string::String {
    fn from(value: Generation) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for Generation {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 32usize {
            return Err("longer than 32 characters".into());
        }
        if value.chars().count() < 32usize {
            return Err("shorter than 32 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[a-f0-9]{32}$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[a-f0-9]{32}$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for Generation {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for Generation {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for Generation {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`Nonce`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct Nonce(::std::string::String);
impl ::std::ops::Deref for Nonce {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<Nonce> for ::std::string::String {
    fn from(value: Nonce) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for Nonce {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 64usize {
            return Err("longer than 64 characters".into());
        }
        if value.chars().count() < 64usize {
            return Err("shorter than 64 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[a-f0-9]{64}$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[a-f0-9]{64}$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for Nonce {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for Nonce {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for Nonce {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`Ping`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Ping {
    pub generation: Generation,
    pub mac: Signature,
    pub protocol_version: PingProtocolVersion,
    pub sequence: ::std::num::NonZeroU64,
    #[serde(rename = "type")]
    pub type_: PingType,
}
///`PingProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct PingProtocolVersion(i64);
impl ::std::ops::Deref for PingProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<PingProtocolVersion> for i64 {
    fn from(value: PingProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for PingProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for PingProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`PingType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum PingType {
    #[serde(rename = "ping")]
    Ping,
}
impl ::std::fmt::Display for PingType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Ping => f.write_str("ping"),
        }
    }
}
impl ::std::str::FromStr for PingType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "ping" => Ok(Self::Ping),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for PingType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for PingType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`Pong`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Pong {
    pub generation: Generation,
    pub mac: Signature,
    pub protocol_version: PongProtocolVersion,
    pub sequence: ::std::num::NonZeroU64,
    #[serde(rename = "type")]
    pub type_: PongType,
}
///`PongProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct PongProtocolVersion(i64);
impl ::std::ops::Deref for PongProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<PongProtocolVersion> for i64 {
    fn from(value: PongProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for PongProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for PongProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`PongType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum PongType {
    #[serde(rename = "pong")]
    Pong,
}
impl ::std::fmt::Display for PongType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Pong => f.write_str("pong"),
        }
    }
}
impl ::std::str::FromStr for PongType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "pong" => Ok(Self::Pong),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for PongType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for PongType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ProtocolError`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ProtocolError {
    pub code: ProtocolErrorCode,
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub generation: ::std::option::Option<Generation>,
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub mac: ::std::option::Option<Signature>,
    pub protocol_version: ProtocolErrorProtocolVersion,
    #[serde(rename = "type")]
    pub type_: ProtocolErrorType,
}
///`ProtocolErrorCode`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ProtocolErrorCode {
    #[serde(rename = "authentication_failed")]
    AuthenticationFailed,
    #[serde(rename = "incompatible_version")]
    IncompatibleVersion,
    #[serde(rename = "invalid_message")]
    InvalidMessage,
    #[serde(rename = "message_too_large")]
    MessageTooLarge,
    #[serde(rename = "unexpected_message")]
    UnexpectedMessage,
    #[serde(rename = "stale_generation")]
    StaleGeneration,
    #[serde(rename = "heartbeat_timeout")]
    HeartbeatTimeout,
    #[serde(rename = "session_replaced")]
    SessionReplaced,
    #[serde(rename = "server_busy")]
    ServerBusy,
}
impl ::std::fmt::Display for ProtocolErrorCode {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::AuthenticationFailed => f.write_str("authentication_failed"),
            Self::IncompatibleVersion => f.write_str("incompatible_version"),
            Self::InvalidMessage => f.write_str("invalid_message"),
            Self::MessageTooLarge => f.write_str("message_too_large"),
            Self::UnexpectedMessage => f.write_str("unexpected_message"),
            Self::StaleGeneration => f.write_str("stale_generation"),
            Self::HeartbeatTimeout => f.write_str("heartbeat_timeout"),
            Self::SessionReplaced => f.write_str("session_replaced"),
            Self::ServerBusy => f.write_str("server_busy"),
        }
    }
}
impl ::std::str::FromStr for ProtocolErrorCode {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "authentication_failed" => Ok(Self::AuthenticationFailed),
            "incompatible_version" => Ok(Self::IncompatibleVersion),
            "invalid_message" => Ok(Self::InvalidMessage),
            "message_too_large" => Ok(Self::MessageTooLarge),
            "unexpected_message" => Ok(Self::UnexpectedMessage),
            "stale_generation" => Ok(Self::StaleGeneration),
            "heartbeat_timeout" => Ok(Self::HeartbeatTimeout),
            "session_replaced" => Ok(Self::SessionReplaced),
            "server_busy" => Ok(Self::ServerBusy),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ProtocolErrorCode {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ProtocolErrorCode {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ProtocolErrorProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct ProtocolErrorProtocolVersion(i64);
impl ::std::ops::Deref for ProtocolErrorProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<ProtocolErrorProtocolVersion> for i64 {
    fn from(value: ProtocolErrorProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for ProtocolErrorProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for ProtocolErrorProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`ProtocolErrorType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ProtocolErrorType {
    #[serde(rename = "error")]
    Error,
}
impl ::std::fmt::Display for ProtocolErrorType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Error => f.write_str("error"),
        }
    }
}
impl ::std::str::FromStr for ProtocolErrorType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "error" => Ok(Self::Error),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ProtocolErrorType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ProtocolErrorType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`Signature`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct Signature(::std::string::String);
impl ::std::ops::Deref for Signature {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<Signature> for ::std::string::String {
    fn from(value: Signature) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for Signature {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 64usize {
            return Err("longer than 64 characters".into());
        }
        if value.chars().count() < 64usize {
            return Err("shorter than 64 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[a-f0-9]{64}$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[a-f0-9]{64}$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for Signature {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for Signature {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for Signature {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`Welcome`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Welcome {
    pub capabilities: Capabilities,
    pub generation: Generation,
    pub protocol_version: WelcomeProtocolVersion,
    pub server_signature: Signature,
    #[serde(rename = "type")]
    pub type_: WelcomeType,
}
///`WelcomeProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct WelcomeProtocolVersion(i64);
impl ::std::ops::Deref for WelcomeProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<WelcomeProtocolVersion> for i64 {
    fn from(value: WelcomeProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for WelcomeProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![1_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for WelcomeProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`WelcomeType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum WelcomeType {
    #[serde(rename = "welcome")]
    Welcome,
}
impl ::std::fmt::Display for WelcomeType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Welcome => f.write_str("welcome"),
        }
    }
}
impl ::std::str::FromStr for WelcomeType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "welcome" => Ok(Self::Welcome),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for WelcomeType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for WelcomeType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
/// Error types.
pub mod error {
    /// Error from a `TryFrom` or `FromStr` implementation.
    pub struct ConversionError(::std::borrow::Cow<'static, str>);
    impl ::std::error::Error for ConversionError {}
    impl ::std::fmt::Display for ConversionError {
        fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> Result<(), ::std::fmt::Error> {
            ::std::fmt::Display::fmt(&self.0, f)
        }
    }
    impl ::std::fmt::Debug for ConversionError {
        fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> Result<(), ::std::fmt::Error> {
            ::std::fmt::Debug::fmt(&self.0, f)
        }
    }
    impl From<&'static str> for ConversionError {
        fn from(value: &'static str) -> Self {
            Self(value.into())
        }
    }
    impl From<String> for ConversionError {
        fn from(value: String) -> Self {
            Self(value.into())
        }
    }
}
