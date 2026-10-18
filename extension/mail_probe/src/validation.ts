export { messageDetails } from './message_details.js';

const actions = new Set([
  'inventory',
  'save',
  'send',
  'query',
  'list',
  'get_message',
  'begin_new',
  'update_compose',
  'save_compose',
  'inspect_native_compose',
  'close_compose',
  'select_draft',
  'select_folder',
  'permission_status',
  'open_permission_page',
]);

export function objectValue(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Expected an object.');
  }
  return value as Record<string, unknown>;
}

export function integerValue(value: unknown): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) {
    throw new Error('Expected a nonnegative integer identifier.');
  }
  return value;
}

export function stringValue(value: unknown): string {
  if (typeof value !== 'string' || value.length > 16384) {
    throw new Error('Expected a bounded string.');
  }
  return value;
}

export interface Command {
  id: string;
  action: string;
  arguments: Record<string, unknown>;
}

export function parseCommand(value: unknown): Command {
  const command = objectValue(value);
  const identifier = stringValue(command.id);
  const action = stringValue(command.action);
  if (!/^[a-zA-Z0-9_-]{1,100}$/.test(identifier) || !actions.has(action)) {
    throw new Error('Invalid probe command.');
  }
  return {
    id: identifier,
    action,
    arguments: objectValue(command.arguments ?? {}),
  };
}

export function parseConfiguration(value: unknown) {
  const settings = objectValue(value);
  const endpoint = stringValue(settings.endpoint);
  const token = stringValue(settings.token);
  const address = new URL(endpoint);
  if (
    !['ws:', 'wss:'].includes(address.protocol) ||
    address.username ||
    address.password ||
    address.search ||
    address.hash ||
    !/^[a-f0-9]{64}$/.test(token)
  ) {
    throw new Error('Invalid mail probe configuration.');
  }
  return { endpoint, token };
}
