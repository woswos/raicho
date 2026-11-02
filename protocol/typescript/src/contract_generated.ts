// Generated from protocol/schema/connector.schema.json.

export type ConnectorMessage =
  Challenge | Authenticate | Welcome | Ping | Pong | ProtocolError | Request | Cancel | Reply;
export type Nonce = string;
/**
 * @maxItems 0
 */
export type Capabilities = [];
export type Signature = string;
export type Generation = string;
export type RequestId = number;
export type Operation = ListAccounts | ListMailboxes | ListMessages | ContinueList | CloseList;
export type Handle = string;
export type Outcome = AccountsResult | MailboxesResult | MessagesResult | ClosedResult | FailedResult;
export type MailboxRole = 'inbox' | 'drafts' | 'sent' | 'trash' | 'archive' | 'junk' | 'templates' | 'outbox';
export type MailError =
  'invalid_request' | 'stale_handle' | 'stale_cursor' | 'unsupported' | 'busy' | 'too_large' | 'failed';

export interface Challenge {
  type: 'challenge';
  protocol_version: 2;
  server_nonce: Nonce;
}
export interface Authenticate {
  type: 'authenticate';
  protocol_version: 2;
  backend_kind: string;
  backend_version: string;
  connector_version: string;
  capabilities: Capabilities;
  client_nonce: Nonce;
  client_proof: Signature;
}
export interface Welcome {
  type: 'welcome';
  protocol_version: 2;
  generation: Generation;
  capabilities: Capabilities;
  server_signature: Signature;
}
export interface Ping {
  type: 'ping';
  protocol_version: 2;
  generation: Generation;
  sequence: number;
  mac: Signature;
}
export interface Pong {
  type: 'pong';
  protocol_version: 2;
  generation: Generation;
  sequence: number;
  mac: Signature;
}
export interface ProtocolError {
  type: 'error';
  protocol_version: 2;
  generation?: Generation;
  code:
    | 'authentication_failed'
    | 'incompatible_version'
    | 'invalid_message'
    | 'message_too_large'
    | 'unexpected_message'
    | 'stale_generation'
    | 'heartbeat_timeout'
    | 'session_replaced'
    | 'server_busy';
  mac?: Signature;
}
export interface Request {
  type: 'request';
  protocol_version: 2;
  generation: Generation;
  request_id: RequestId;
  operation: Operation;
  mac: Signature;
}
export interface ListAccounts {
  name: 'list_accounts';
}
export interface ListMailboxes {
  name: 'list_mailboxes';
  account: Handle;
}
export interface ListMessages {
  name: 'list_messages';
  mailbox: Handle;
}
export interface ContinueList {
  name: 'continue_list';
  cursor: Handle;
}
export interface CloseList {
  name: 'close_list';
  cursor: Handle;
}
export interface Cancel {
  type: 'cancel';
  protocol_version: 2;
  generation: Generation;
  request_id: RequestId;
  mac: Signature;
}
export interface Reply {
  type: 'reply';
  protocol_version: 2;
  generation: Generation;
  request_id: RequestId;
  result: Outcome;
  mac: Signature;
}
export interface AccountsResult {
  kind: 'accounts';
  accounts: Account[];
}
export interface Account {
  id: Handle;
  name: string;
  identities: Identity[];
}
export interface Identity {
  id: Handle;
  name: string;
  email: string;
}
export interface MailboxesResult {
  kind: 'mailboxes';
  mailboxes: Mailbox[];
  cursor?: Handle;
}
export interface Mailbox {
  id: Handle;
  name: string;
  parent?: Handle;
  role?: MailboxRole;
}
export interface MessagesResult {
  kind: 'messages';
  messages: MessageSummary[];
  cursor?: Handle;
}
export interface MessageSummary {
  id: Handle;
  subject: string;
  author: string;
  recipients: string;
  date: string;
  read: boolean;
  flagged: boolean;
}
export interface ClosedResult {
  kind: 'closed';
}
export interface FailedResult {
  kind: 'error';
  code: MailError;
}
