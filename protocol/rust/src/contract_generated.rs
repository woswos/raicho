// Generated from protocol/schema/connector.schema.json.
///`Account`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Account {
    pub id: Handle,
    pub identities: ::std::vec::Vec<Identity>,
    pub name: AccountName,
}
///`AccountName`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct AccountName(::std::string::String);
impl ::std::ops::Deref for AccountName {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<AccountName> for ::std::string::String {
    fn from(value: AccountName) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for AccountName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 128usize {
            return Err("longer than 128 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for AccountName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AccountName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for AccountName {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`AccountsResult`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct AccountsResult {
    pub accounts: ::std::vec::Vec<Account>,
    pub kind: AccountsResultKind,
}
///`AccountsResultKind`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum AccountsResultKind {
    #[serde(rename = "accounts")]
    Accounts,
}
impl ::std::fmt::Display for AccountsResultKind {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Accounts => f.write_str("accounts"),
        }
    }
}
impl ::std::str::FromStr for AccountsResultKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "accounts" => Ok(Self::Accounts),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for AccountsResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AccountsResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
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
        if ![2_i64].contains(&value) {
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
///`Cancel`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Cancel {
    pub generation: Generation,
    pub mac: Signature,
    pub protocol_version: CancelProtocolVersion,
    pub request_id: RequestId,
    #[serde(rename = "type")]
    pub type_: CancelType,
}
///`CancelProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct CancelProtocolVersion(i64);
impl ::std::ops::Deref for CancelProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<CancelProtocolVersion> for i64 {
    fn from(value: CancelProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for CancelProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![2_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for CancelProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`CancelType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum CancelType {
    #[serde(rename = "cancel")]
    Cancel,
}
impl ::std::fmt::Display for CancelType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Cancel => f.write_str("cancel"),
        }
    }
}
impl ::std::str::FromStr for CancelType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "cancel" => Ok(Self::Cancel),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for CancelType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for CancelType {
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
        if ![2_i64].contains(&value) {
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
///`CloseList`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct CloseList {
    pub cursor: Handle,
    pub name: CloseListName,
}
///`CloseListName`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum CloseListName {
    #[serde(rename = "close_list")]
    CloseList,
}
impl ::std::fmt::Display for CloseListName {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::CloseList => f.write_str("close_list"),
        }
    }
}
impl ::std::str::FromStr for CloseListName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "close_list" => Ok(Self::CloseList),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for CloseListName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for CloseListName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ClosedResult`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ClosedResult {
    pub kind: ClosedResultKind,
}
///`ClosedResultKind`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ClosedResultKind {
    #[serde(rename = "closed")]
    Closed,
}
impl ::std::fmt::Display for ClosedResultKind {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Closed => f.write_str("closed"),
        }
    }
}
impl ::std::str::FromStr for ClosedResultKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "closed" => Ok(Self::Closed),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ClosedResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ClosedResultKind {
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
    Request(Request),
    Cancel(Cancel),
    Reply(Reply),
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
impl ::std::convert::From<Request> for ConnectorMessage {
    fn from(value: Request) -> Self {
        Self::Request(value)
    }
}
impl ::std::convert::From<Cancel> for ConnectorMessage {
    fn from(value: Cancel) -> Self {
        Self::Cancel(value)
    }
}
impl ::std::convert::From<Reply> for ConnectorMessage {
    fn from(value: Reply) -> Self {
        Self::Reply(value)
    }
}
///`ContinueList`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ContinueList {
    pub cursor: Handle,
    pub name: ContinueListName,
}
///`ContinueListName`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ContinueListName {
    #[serde(rename = "continue_list")]
    ContinueList,
}
impl ::std::fmt::Display for ContinueListName {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::ContinueList => f.write_str("continue_list"),
        }
    }
}
impl ::std::str::FromStr for ContinueListName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "continue_list" => Ok(Self::ContinueList),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ContinueListName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ContinueListName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`FailedResult`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct FailedResult {
    pub code: MailError,
    pub kind: FailedResultKind,
}
///`FailedResultKind`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum FailedResultKind {
    #[serde(rename = "error")]
    Error,
}
impl ::std::fmt::Display for FailedResultKind {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Error => f.write_str("error"),
        }
    }
}
impl ::std::str::FromStr for FailedResultKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "error" => Ok(Self::Error),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for FailedResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for FailedResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
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
///`Handle`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct Handle(::std::string::String);
impl ::std::ops::Deref for Handle {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<Handle> for ::std::string::String {
    fn from(value: Handle) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for Handle {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 22usize {
            return Err("longer than 22 characters".into());
        }
        if value.chars().count() < 22usize {
            return Err("shorter than 22 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> =
            ::std::sync::LazyLock::new(|| ::regress::Regex::new("^[A-Za-z0-9_-]{22}$").unwrap());
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[A-Za-z0-9_-]{22}$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for Handle {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for Handle {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for Handle {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`Identity`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Identity {
    pub email: IdentityEmail,
    pub id: Handle,
    pub name: IdentityName,
}
///`IdentityEmail`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct IdentityEmail(::std::string::String);
impl ::std::ops::Deref for IdentityEmail {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<IdentityEmail> for ::std::string::String {
    fn from(value: IdentityEmail) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for IdentityEmail {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 254usize {
            return Err("longer than 254 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for IdentityEmail {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for IdentityEmail {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for IdentityEmail {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`IdentityName`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct IdentityName(::std::string::String);
impl ::std::ops::Deref for IdentityName {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<IdentityName> for ::std::string::String {
    fn from(value: IdentityName) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for IdentityName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 128usize {
            return Err("longer than 128 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for IdentityName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for IdentityName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for IdentityName {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`ListAccounts`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ListAccounts {
    pub name: ListAccountsName,
}
///`ListAccountsName`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ListAccountsName {
    #[serde(rename = "list_accounts")]
    ListAccounts,
}
impl ::std::fmt::Display for ListAccountsName {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::ListAccounts => f.write_str("list_accounts"),
        }
    }
}
impl ::std::str::FromStr for ListAccountsName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "list_accounts" => Ok(Self::ListAccounts),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ListAccountsName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ListAccountsName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ListMailboxes`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ListMailboxes {
    pub account: Handle,
    pub name: ListMailboxesName,
}
///`ListMailboxesName`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ListMailboxesName {
    #[serde(rename = "list_mailboxes")]
    ListMailboxes,
}
impl ::std::fmt::Display for ListMailboxesName {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::ListMailboxes => f.write_str("list_mailboxes"),
        }
    }
}
impl ::std::str::FromStr for ListMailboxesName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "list_mailboxes" => Ok(Self::ListMailboxes),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ListMailboxesName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ListMailboxesName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`ListMessages`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct ListMessages {
    pub mailbox: Handle,
    pub name: ListMessagesName,
}
///`ListMessagesName`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ListMessagesName {
    #[serde(rename = "list_messages")]
    ListMessages,
}
impl ::std::fmt::Display for ListMessagesName {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::ListMessages => f.write_str("list_messages"),
        }
    }
}
impl ::std::str::FromStr for ListMessagesName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "list_messages" => Ok(Self::ListMessages),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ListMessagesName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ListMessagesName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`MailError`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum MailError {
    #[serde(rename = "invalid_request")]
    InvalidRequest,
    #[serde(rename = "stale_handle")]
    StaleHandle,
    #[serde(rename = "stale_cursor")]
    StaleCursor,
    #[serde(rename = "unsupported")]
    Unsupported,
    #[serde(rename = "busy")]
    Busy,
    #[serde(rename = "too_large")]
    TooLarge,
    #[serde(rename = "failed")]
    Failed,
}
impl ::std::fmt::Display for MailError {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::InvalidRequest => f.write_str("invalid_request"),
            Self::StaleHandle => f.write_str("stale_handle"),
            Self::StaleCursor => f.write_str("stale_cursor"),
            Self::Unsupported => f.write_str("unsupported"),
            Self::Busy => f.write_str("busy"),
            Self::TooLarge => f.write_str("too_large"),
            Self::Failed => f.write_str("failed"),
        }
    }
}
impl ::std::str::FromStr for MailError {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "invalid_request" => Ok(Self::InvalidRequest),
            "stale_handle" => Ok(Self::StaleHandle),
            "stale_cursor" => Ok(Self::StaleCursor),
            "unsupported" => Ok(Self::Unsupported),
            "busy" => Ok(Self::Busy),
            "too_large" => Ok(Self::TooLarge),
            "failed" => Ok(Self::Failed),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for MailError {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MailError {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`Mailbox`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Mailbox {
    pub id: Handle,
    pub name: MailboxName,
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub parent: ::std::option::Option<Handle>,
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub role: ::std::option::Option<MailboxRole>,
}
///`MailboxName`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct MailboxName(::std::string::String);
impl ::std::ops::Deref for MailboxName {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<MailboxName> for ::std::string::String {
    fn from(value: MailboxName) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for MailboxName {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 255usize {
            return Err("longer than 255 characters".into());
        }
        if value.chars().count() < 1usize {
            return Err("shorter than 1 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for MailboxName {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MailboxName {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for MailboxName {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`MailboxRole`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum MailboxRole {
    #[serde(rename = "inbox")]
    Inbox,
    #[serde(rename = "drafts")]
    Drafts,
    #[serde(rename = "sent")]
    Sent,
    #[serde(rename = "trash")]
    Trash,
    #[serde(rename = "archive")]
    Archive,
    #[serde(rename = "junk")]
    Junk,
    #[serde(rename = "templates")]
    Templates,
    #[serde(rename = "outbox")]
    Outbox,
}
impl ::std::fmt::Display for MailboxRole {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Inbox => f.write_str("inbox"),
            Self::Drafts => f.write_str("drafts"),
            Self::Sent => f.write_str("sent"),
            Self::Trash => f.write_str("trash"),
            Self::Archive => f.write_str("archive"),
            Self::Junk => f.write_str("junk"),
            Self::Templates => f.write_str("templates"),
            Self::Outbox => f.write_str("outbox"),
        }
    }
}
impl ::std::str::FromStr for MailboxRole {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "inbox" => Ok(Self::Inbox),
            "drafts" => Ok(Self::Drafts),
            "sent" => Ok(Self::Sent),
            "trash" => Ok(Self::Trash),
            "archive" => Ok(Self::Archive),
            "junk" => Ok(Self::Junk),
            "templates" => Ok(Self::Templates),
            "outbox" => Ok(Self::Outbox),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for MailboxRole {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MailboxRole {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`MailboxesResult`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct MailboxesResult {
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub cursor: ::std::option::Option<Handle>,
    pub kind: MailboxesResultKind,
    pub mailboxes: ::std::vec::Vec<Mailbox>,
}
///`MailboxesResultKind`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum MailboxesResultKind {
    #[serde(rename = "mailboxes")]
    Mailboxes,
}
impl ::std::fmt::Display for MailboxesResultKind {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Mailboxes => f.write_str("mailboxes"),
        }
    }
}
impl ::std::str::FromStr for MailboxesResultKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "mailboxes" => Ok(Self::Mailboxes),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for MailboxesResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MailboxesResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`MessageSummary`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct MessageSummary {
    pub author: MessageSummaryAuthor,
    pub date: MessageSummaryDate,
    pub flagged: bool,
    pub id: Handle,
    pub read: bool,
    pub recipients: MessageSummaryRecipients,
    pub subject: MessageSummarySubject,
}
///`MessageSummaryAuthor`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct MessageSummaryAuthor(::std::string::String);
impl ::std::ops::Deref for MessageSummaryAuthor {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<MessageSummaryAuthor> for ::std::string::String {
    fn from(value: MessageSummaryAuthor) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for MessageSummaryAuthor {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 300usize {
            return Err("longer than 300 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for MessageSummaryAuthor {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MessageSummaryAuthor {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for MessageSummaryAuthor {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`MessageSummaryDate`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct MessageSummaryDate(::std::string::String);
impl ::std::ops::Deref for MessageSummaryDate {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<MessageSummaryDate> for ::std::string::String {
    fn from(value: MessageSummaryDate) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for MessageSummaryDate {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 20usize {
            return Err("longer than 20 characters".into());
        }
        if value.chars().count() < 20usize {
            return Err("shorter than 20 characters".into());
        }
        static PATTERN: ::std::sync::LazyLock<::regress::Regex> = ::std::sync::LazyLock::new(|| {
            ::regress::Regex::new("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$").unwrap()
        });
        if PATTERN.find(value).is_none() {
            return Err("doesn't match pattern \"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$\"".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for MessageSummaryDate {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MessageSummaryDate {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for MessageSummaryDate {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`MessageSummaryRecipients`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct MessageSummaryRecipients(::std::string::String);
impl ::std::ops::Deref for MessageSummaryRecipients {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<MessageSummaryRecipients> for ::std::string::String {
    fn from(value: MessageSummaryRecipients) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for MessageSummaryRecipients {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 300usize {
            return Err("longer than 300 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for MessageSummaryRecipients {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MessageSummaryRecipients {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for MessageSummaryRecipients {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`MessageSummarySubject`
#[derive(::serde::Serialize, Clone, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[serde(transparent)]
pub struct MessageSummarySubject(::std::string::String);
impl ::std::ops::Deref for MessageSummarySubject {
    type Target = ::std::string::String;
    fn deref(&self) -> &::std::string::String {
        &self.0
    }
}
impl ::std::convert::From<MessageSummarySubject> for ::std::string::String {
    fn from(value: MessageSummarySubject) -> Self {
        value.0
    }
}
impl ::std::str::FromStr for MessageSummarySubject {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        if value.chars().count() > 300usize {
            return Err("longer than 300 characters".into());
        }
        Ok(Self(value.to_string()))
    }
}
impl ::std::convert::TryFrom<&str> for MessageSummarySubject {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MessageSummarySubject {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl<'de> ::serde::Deserialize<'de> for MessageSummarySubject {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        ::std::string::String::deserialize(deserializer)?
            .parse()
            .map_err(|e: self::error::ConversionError| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`MessagesResult`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct MessagesResult {
    #[serde(skip_serializing_if = "::std::option::Option::is_none")]
    pub cursor: ::std::option::Option<Handle>,
    pub kind: MessagesResultKind,
    pub messages: ::std::vec::Vec<MessageSummary>,
}
///`MessagesResultKind`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum MessagesResultKind {
    #[serde(rename = "messages")]
    Messages,
}
impl ::std::fmt::Display for MessagesResultKind {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Messages => f.write_str("messages"),
        }
    }
}
impl ::std::str::FromStr for MessagesResultKind {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "messages" => Ok(Self::Messages),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for MessagesResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for MessagesResultKind {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
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
///`Operation`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(untagged)]
pub enum Operation {
    ListAccounts(ListAccounts),
    ListMailboxes(ListMailboxes),
    ListMessages(ListMessages),
    ContinueList(ContinueList),
    CloseList(CloseList),
}
impl ::std::convert::From<ListAccounts> for Operation {
    fn from(value: ListAccounts) -> Self {
        Self::ListAccounts(value)
    }
}
impl ::std::convert::From<ListMailboxes> for Operation {
    fn from(value: ListMailboxes) -> Self {
        Self::ListMailboxes(value)
    }
}
impl ::std::convert::From<ListMessages> for Operation {
    fn from(value: ListMessages) -> Self {
        Self::ListMessages(value)
    }
}
impl ::std::convert::From<ContinueList> for Operation {
    fn from(value: ContinueList) -> Self {
        Self::ContinueList(value)
    }
}
impl ::std::convert::From<CloseList> for Operation {
    fn from(value: CloseList) -> Self {
        Self::CloseList(value)
    }
}
///`Outcome`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(untagged)]
pub enum Outcome {
    AccountsResult(AccountsResult),
    MailboxesResult(MailboxesResult),
    MessagesResult(MessagesResult),
    ClosedResult(ClosedResult),
    FailedResult(FailedResult),
}
impl ::std::convert::From<AccountsResult> for Outcome {
    fn from(value: AccountsResult) -> Self {
        Self::AccountsResult(value)
    }
}
impl ::std::convert::From<MailboxesResult> for Outcome {
    fn from(value: MailboxesResult) -> Self {
        Self::MailboxesResult(value)
    }
}
impl ::std::convert::From<MessagesResult> for Outcome {
    fn from(value: MessagesResult) -> Self {
        Self::MessagesResult(value)
    }
}
impl ::std::convert::From<ClosedResult> for Outcome {
    fn from(value: ClosedResult) -> Self {
        Self::ClosedResult(value)
    }
}
impl ::std::convert::From<FailedResult> for Outcome {
    fn from(value: FailedResult) -> Self {
        Self::FailedResult(value)
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
        if ![2_i64].contains(&value) {
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
        if ![2_i64].contains(&value) {
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
        if ![2_i64].contains(&value) {
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
///`Reply`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Reply {
    pub generation: Generation,
    pub mac: Signature,
    pub protocol_version: ReplyProtocolVersion,
    pub request_id: RequestId,
    pub result: Outcome,
    #[serde(rename = "type")]
    pub type_: ReplyType,
}
///`ReplyProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct ReplyProtocolVersion(i64);
impl ::std::ops::Deref for ReplyProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<ReplyProtocolVersion> for i64 {
    fn from(value: ReplyProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for ReplyProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![2_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for ReplyProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`ReplyType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ReplyType {
    #[serde(rename = "reply")]
    Reply,
}
impl ::std::fmt::Display for ReplyType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Reply => f.write_str("reply"),
        }
    }
}
impl ::std::str::FromStr for ReplyType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "reply" => Ok(Self::Reply),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for ReplyType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for ReplyType {
    type Error = self::error::ConversionError;
    fn try_from(value: ::std::string::String) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
///`Request`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub generation: Generation,
    pub mac: Signature,
    pub operation: Operation,
    pub protocol_version: RequestProtocolVersion,
    pub request_id: RequestId,
    #[serde(rename = "type")]
    pub type_: RequestType,
}
///`RequestId`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct RequestId(pub ::std::num::NonZeroU64);
impl ::std::ops::Deref for RequestId {
    type Target = ::std::num::NonZeroU64;
    fn deref(&self) -> &::std::num::NonZeroU64 {
        &self.0
    }
}
impl ::std::convert::From<RequestId> for ::std::num::NonZeroU64 {
    fn from(value: RequestId) -> Self {
        value.0
    }
}
impl ::std::convert::From<::std::num::NonZeroU64> for RequestId {
    fn from(value: ::std::num::NonZeroU64) -> Self {
        Self(value)
    }
}
impl ::std::fmt::Display for RequestId {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        self.0.fmt(f)
    }
}
impl ::std::str::FromStr for RequestId {
    type Err = <::std::num::NonZeroU64 as ::std::str::FromStr>::Err;
    fn from_str(value: &str) -> ::std::result::Result<Self, Self::Err> {
        Ok(Self(value.parse()?))
    }
}
impl ::std::convert::TryFrom<&str> for RequestId {
    type Error = <::std::num::NonZeroU64 as ::std::str::FromStr>::Err;
    fn try_from(value: &str) -> ::std::result::Result<Self, Self::Error> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<String> for RequestId {
    type Error = <::std::num::NonZeroU64 as ::std::str::FromStr>::Err;
    fn try_from(value: String) -> ::std::result::Result<Self, Self::Error> {
        value.parse()
    }
}
///`RequestProtocolVersion`
#[derive(::serde::Serialize, Clone)]
#[serde(transparent)]
pub struct RequestProtocolVersion(i64);
impl ::std::ops::Deref for RequestProtocolVersion {
    type Target = i64;
    fn deref(&self) -> &i64 {
        &self.0
    }
}
impl ::std::convert::From<RequestProtocolVersion> for i64 {
    fn from(value: RequestProtocolVersion) -> Self {
        value.0
    }
}
impl ::std::convert::TryFrom<i64> for RequestProtocolVersion {
    type Error = self::error::ConversionError;
    fn try_from(value: i64) -> ::std::result::Result<Self, self::error::ConversionError> {
        if ![2_i64].contains(&value) {
            Err("invalid value".into())
        } else {
            Ok(Self(value))
        }
    }
}
impl<'de> ::serde::Deserialize<'de> for RequestProtocolVersion {
    fn deserialize<D>(deserializer: D) -> ::std::result::Result<Self, D::Error>
    where
        D: ::serde::Deserializer<'de>,
    {
        Self::try_from(<i64>::deserialize(deserializer)?)
            .map_err(|e| <D::Error as ::serde::de::Error>::custom(e.to_string()))
    }
}
///`RequestType`
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum RequestType {
    #[serde(rename = "request")]
    Request,
}
impl ::std::fmt::Display for RequestType {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Request => f.write_str("request"),
        }
    }
}
impl ::std::str::FromStr for RequestType {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "request" => Ok(Self::Request),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for RequestType {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for RequestType {
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
        if ![2_i64].contains(&value) {
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
