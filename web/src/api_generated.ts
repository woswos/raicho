// Generated from protocol/schema/api.schema.json.

export type ApiDocument =
  SessionDocument | PreferencesDocument | AccountsDocument | MailboxesDocument | MessagesDocument | ErrorDocument;
export type Theme = 'system' | 'light' | 'dark';
export type Handle = string;
export type MailboxRole = 'inbox' | 'drafts' | 'sent' | 'trash' | 'archive' | 'junk' | 'templates' | 'outbox';
export type Cursor = string;
export type ApiError =
  | 'unauthenticated'
  | 'forbidden_origin'
  | 'invalid_request'
  | 'rate_limited'
  | 'invalid_password'
  | 'login_unconfigured'
  | 'storage_unavailable'
  | 'backend_disconnected'
  | 'backend_busy'
  | 'backend_timeout'
  | 'stale_handle'
  | 'stale_cursor'
  | 'unsupported'
  | 'backend_failed';

export interface SessionDocument {
  authenticated: true;
}
export interface PreferencesDocument {
  theme: Theme;
}
export interface AccountsDocument {
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
export interface MailboxesDocument {
  mailboxes: Mailbox[];
  truncated: boolean;
}
export interface Mailbox {
  id: Handle;
  name: string;
  parent?: Handle;
  role?: MailboxRole;
}
export interface MessagesDocument {
  messages: MessageSummary[];
  cursor?: Cursor;
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
export interface ErrorDocument {
  error: ApiError;
}
