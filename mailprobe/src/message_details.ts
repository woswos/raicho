import { objectValue, stringValue } from './validation.js';

const stringFields = new Set([
  'subject',
  'identityId',
  'from',
  'body',
  'plainTextBody',
  'deliveryFormat',
]);
const recipientFields = new Set(['to', 'cc', 'bcc', 'replyTo']);

export interface Attachment {
  file: File;
  name: string;
}

export interface Details extends Record<string, unknown> {
  attachments?: Attachment[];
}

export function messageDetails(value: unknown, requireSubject = true): Details {
  const source = objectValue(value);
  const details: Details = {};
  if (requireSubject) stringValue(source.subject);
  for (const [name, item] of Object.entries(source)) {
    if (stringFields.has(name)) {
      details[name] = stringValue(item);
    } else if (recipientFields.has(name)) {
      if (Array.isArray(item)) {
        if (item.length > 20) throw new Error('Too many fixture recipients.');
        details[name] = item.map(stringValue);
      } else details[name] = stringValue(item);
    } else if (name === 'isPlainText' || name === 'isModified') {
      if (typeof item !== 'boolean') throw new Error('Expected a boolean.');
      details[name] = item;
    } else if (name === 'attachments') {
      if (!Array.isArray(item) || item.length > 3) {
        throw new Error('Expected at most three fixture attachments.');
      }
      details.attachments = item.map(attachmentValue);
    } else if (
      name === 'overrideDefaultFccFolder' ||
      name === 'additionalFccFolder'
    ) {
      details[name] = item === '' ? '' : objectValue(item);
    } else throw new Error('Unsupported fixture message field.');
  }
  return details;
}

function attachmentValue(value: unknown): Attachment {
  const attachment = objectValue(value);
  const name = stringValue(attachment.name);
  const content = stringValue(attachment.content);
  const type = stringValue(attachment.type ?? 'text/plain');
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,99}$/.test(name)) {
    throw new Error('Invalid fixture attachment name.');
  }
  return { name, file: new File([content], name, { type }) };
}
