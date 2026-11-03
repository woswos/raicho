// Generated from protocol/schema/api.schema.json.

export type ApiDocument = AccountsDocument | MailboxesDocument | MessagesDocument | ErrorDocument;
export type Handle = string;
export type MailboxRole = 'inbox' | 'drafts' | 'sent' | 'trash' | 'archive' | 'junk' | 'templates' | 'outbox';
export type Cursor = string;
export type ApiError =
  | 'invalid_request'
  | 'backend_disconnected'
  | 'backend_busy'
  | 'backend_timeout'
  | 'stale_handle'
  | 'stale_cursor'
  | 'unsupported'
  | 'backend_failed';

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
