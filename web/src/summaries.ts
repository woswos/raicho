import type { MessageSummary } from './api_generated.js';

/** Adds a page after the summaries already shown, without repeating a message. */
export function appendSummaries(existing: MessageSummary[], page: MessageSummary[]): MessageSummary[] {
  const seen = new Set(existing.map((summary) => summary.id));
  return [...existing, ...page.filter((summary) => !seen.has(summary.id))];
}

/** A short date: the time for today, the day for this year, and the full date otherwise. */
export function shortDate(value: string, now: Date, locale?: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime()) || date.getTime() === 0) return '';
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString(locale, {
    day: 'numeric',
    month: 'short',
    ...(date.getFullYear() === now.getFullYear() ? {} : { year: 'numeric' }),
  });
}

export function longDate(value: string, locale?: string): string {
  const date = new Date(value);
  return date.getTime() === 0 ? '' : date.toLocaleString(locale, { dateStyle: 'full', timeStyle: 'short' });
}
