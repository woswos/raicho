// The Manifest V2 subset of Thunderbird 153's mail APIs that the read-only adapter uses.

export interface MailIdentity {
  id: string;
  name?: string;
  email?: string;
}

export interface MailAccount {
  id: string;
  name: string;
  type: string;
  identities: MailIdentity[];
}

export interface MailFolder {
  id: string;
  accountId: string;
  name?: string;
  path: string;
  specialUse?: string[];
}

export interface MessageHeader {
  id: number;
  date: Date;
  author: string;
  recipients: string[];
  subject: string;
  read?: boolean;
  flagged?: boolean;
}

export interface MessageList {
  id: string | null;
  messages: MessageHeader[];
}

interface Event<Listener> {
  addListener: (listener: Listener) => void;
}

export interface MailApi {
  accounts: {
    list: (includeSubFolders: boolean) => Promise<MailAccount[]>;
    onDeleted: Event<(accountId: string) => void>;
  };
  folders: {
    query: (queryInfo: Record<string, unknown>) => Promise<MailFolder[]>;
    onRenamed: Event<(original: MailFolder, renamed: MailFolder) => void>;
    onMoved: Event<(original: MailFolder, moved: MailFolder) => void>;
    onDeleted: Event<(folder: MailFolder) => void>;
  };
  messages: {
    list: (folderId: string, options: { sortType: 'date'; sortOrder: 'descending' }) => Promise<MessageList>;
    continueList: (messageListId: string) => Promise<MessageList>;
    abortList: (messageListId: string) => Promise<void>;
    onMoved: Event<(original: MessageList, moved: MessageList) => void>;
    onDeleted: Event<(messages: MessageList) => void>;
  };
}
