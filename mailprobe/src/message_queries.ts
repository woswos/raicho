import type { MailApi, MessageList } from './mail_api.js';
import { objectValue, stringValue } from './validation.js';

export function queryDetails(value: unknown) {
  const source = objectValue(value);
  const query: Record<string, unknown> = {};
  for (const [name, item] of Object.entries(source)) {
    if (!['subject', 'headerMessageId', 'folderId'].includes(name)) {
      throw new Error('Unsupported message query field.');
    }
    query[name] = stringValue(item);
  }
  return query;
}

export async function collectMessages(api: MailApi, page: MessageList) {
  const messages = [...page.messages];
  while (page.id) {
    if (messages.length >= 100) throw new Error('Too many fixture messages.');
    page = await api.messages.continueList(page.id);
    messages.push(...page.messages);
  }
  return { messages };
}

export async function inspectMessage(api: MailApi, identifier: number) {
  const attachments = [];
  for (const attachment of await api.messages.listAttachments(identifier)) {
    if (attachment.size > 16384) throw new Error('Fixture attachment is too large.');
    const content = await api.messages.getAttachmentFile(identifier, attachment.partName);
    attachments.push({ ...attachment, content: await content.text() });
  }
  return {
    header: await api.messages.get(identifier),
    full: await api.messages.getFull(identifier),
    attachments,
  };
}
