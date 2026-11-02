import type { MailboxRole } from '../../protocol/typescript/src/contract_generated.js';

const ROLES: Record<string, MailboxRole> = {
  inbox: 'inbox',
  drafts: 'drafts',
  sent: 'sent',
  trash: 'trash',
  archives: 'archive',
  junk: 'junk',
  templates: 'templates',
  outbox: 'outbox',
};

/** Mail text without control characters or unpaired surrogates, cut to a number of code points. */
export function mailText(value: unknown, maximum: number): string {
  const text = typeof value === 'string' ? value : '';
  // eslint-disable-next-line no-control-regex -- the protocol forbids these characters in mail text
  return Array.from(text.toWellFormed().replace(/[\u0000-\u001f]/gu, ' '))
    .slice(0, maximum)
    .join('');
}

export function mailDate(value: unknown): string {
  const time = value instanceof Date ? value.getTime() : Number.NaN;
  const date = new Date(Number.isFinite(time) && time >= 0 && time < 253402300800000 ? time : 0);
  return date.toISOString().replace(/\.\d{3}Z$/u, 'Z');
}

export function mailboxRole(specialUse: string[] | undefined): MailboxRole | undefined {
  return specialUse?.map((use) => ROLES[use]).find((role) => role !== undefined);
}
