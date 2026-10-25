import type { Details } from './message_details.js';

export interface MessageHeader extends Record<string, unknown> {
  id: number;
}

export interface MessageList {
  id?: string;
  messages: MessageHeader[];
}

export interface Tab extends Record<string, unknown> {
  id: number;
  type?: string;
}

export interface MailApi {
  accounts: { list: (includeFolders: boolean) => Promise<unknown> };
  runtime: {
    getBrowserInfo: () => Promise<{ version: string }>;
    getManifest: () => { version: string };
    openOptionsPage: () => Promise<void>;
  };
  permissions: {
    contains: (permissions: { permissions: string[] }) => Promise<boolean>;
  };
  storage: { managed: { get: () => Promise<unknown> } };
  messages: {
    saveMessage: (
      details: Details,
      options: { mode: 'draft' },
    ) => Promise<unknown>;
    sendMessage: (
      details: Details,
      options: { mode: 'sendNow' | 'sendLater' },
    ) => Promise<unknown>;
    query: (query: Record<string, unknown>) => Promise<MessageList>;
    list: (folderIdentifier: string) => Promise<MessageList>;
    continueList: (identifier: string) => Promise<MessageList>;
    get: (identifier: number) => Promise<MessageHeader>;
    getFull: (identifier: number) => Promise<unknown>;
    listAttachments: (
      identifier: number,
    ) => Promise<{ name: string; partName: string; size: number }[]>;
    getAttachmentFile: (identifier: number, partName: string) => Promise<File>;
  };
  compose: {
    beginNew: (messageIdentifier: number, details: Details) => Promise<Tab>;
    getComposeDetails: (
      tabIdentifier: number,
    ) => Promise<Record<string, unknown>>;
    setComposeDetails: (
      tabIdentifier: number,
      details: Details,
    ) => Promise<void>;
    saveMessage: (
      tabIdentifier: number,
      options: { mode: 'draft' },
    ) => Promise<unknown>;
  };
  tabs: {
    query: (query: Record<string, unknown>) => Promise<Tab[]>;
    remove: (identifier: number) => Promise<void>;
  };
  mailTabs: {
    query: (query: Record<string, unknown>) => Promise<Tab[]>;
    update: (
      tabIdentifier: number,
      properties: {
        displayedFolder: string;
        folderMode: 'all';
      },
    ) => Promise<Tab>;
    setSelectedMessages: (
      tabIdentifier: number,
      messageIdentifiers: number[],
    ) => Promise<void>;
  };
}
