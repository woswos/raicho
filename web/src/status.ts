import type { ApplicationStatus as StatusDocument, BackendStatus as BackendDocument } from './status_generated.js';
import validateStatus from './status_validator_generated.js';

export type BackendStatus = Pick<BackendDocument, 'status' | 'kind' | 'last_error'>;

export interface ApplicationStatus extends Omit<StatusDocument, 'backend'> {
  backend: BackendStatus;
}

export class StatusResponseError extends Error {
  constructor() {
    super('Raicho returned an unexpected status response.');
    this.name = 'StatusResponseError';
  }
}

export function readStatus(value: unknown): ApplicationStatus | undefined {
  if (!validateStatus(value)) return undefined;
  const { status, database, backend, version, commit } = value;
  return {
    status,
    database: { ...database },
    backend: {
      status: backend.status,
      kind: backend.kind,
      last_error: backend.last_error,
    },
    version,
    commit,
  };
}

export function parseStatus(value: unknown): ApplicationStatus {
  const status = readStatus(value);
  if (status === undefined) throw new StatusResponseError();
  return status;
}
