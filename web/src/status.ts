const backendStates = [
  'unconfigured',
  'disconnected',
  'connected',
  'revoked',
  'unavailable',
] as const;
const backendErrors = [
  'authentication_failed',
  'authentication_timeout',
  'incompatible_version',
  'invalid_message',
  'message_too_large',
  'unexpected_message',
  'stale_generation',
  'heartbeat_timeout',
  'disconnected',
  'storage_unavailable',
  'server_busy',
] as const;

export interface BackendStatus {
  status: (typeof backendStates)[number];
  kind: 'thunderbird';
  last_error: (typeof backendErrors)[number] | null;
}

export interface ApplicationStatus {
  status: 'ready';
  database: { status: 'ready'; engine: 'sqlite'; version: string };
  backend: BackendStatus;
  version: string;
  commit: string;
}

export class StatusResponseError extends Error {
  constructor() {
    super('Raicho returned an unexpected status response.');
    this.name = 'StatusResponseError';
  }
}

function readRecord(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new StatusResponseError();
  }
  return value as Record<string, unknown>;
}

function readVersion(value: unknown): string {
  if (
    typeof value !== 'string' ||
    value.trim().length === 0 ||
    value.length > 80
  ) {
    throw new StatusResponseError();
  }
  return value;
}

export function parseStatus(value: unknown): ApplicationStatus {
  const response = readRecord(value);
  const database = readRecord(response['database']);
  const backend = readRecord(response['backend']);
  if (
    response['status'] !== 'ready' ||
    database['status'] !== 'ready' ||
    database['engine'] !== 'sqlite' ||
    backend['kind'] !== 'thunderbird'
  ) {
    throw new StatusResponseError();
  }

  const backendState = backendStates.find(
    (state) => state === backend['status'],
  );
  const backendError =
    backend['last_error'] === null
      ? null
      : backendErrors.find((error) => error === backend['last_error']);
  if (backendState === undefined || backendError === undefined) {
    throw new StatusResponseError();
  }

  return {
    status: 'ready',
    database: {
      status: 'ready',
      engine: 'sqlite',
      version: readVersion(database['version']),
    },
    backend: {
      status: backendState,
      kind: 'thunderbird',
      last_error: backendError,
    },
    version: readVersion(response['version']),
    commit: readVersion(response['commit']),
  };
}
