export interface ApplicationStatus {
  status: 'ready';
  database: { status: 'ready'; engine: 'sqlite'; version: string };
  backend: { status: 'unconfigured'; kind: 'thunderbird' };
  version: string;
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
    backend['status'] !== 'unconfigured' ||
    backend['kind'] !== 'thunderbird'
  ) {
    throw new StatusResponseError();
  }

  return {
    status: 'ready',
    database: {
      status: 'ready',
      engine: 'sqlite',
      version: readVersion(database['version']),
    },
    backend: { status: 'unconfigured', kind: 'thunderbird' },
    version: readVersion(response['version']),
  };
}
