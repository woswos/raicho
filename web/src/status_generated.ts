// Generated from protocol/schema/status.schema.json.

/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "Readiness".
 */
export type Readiness = 'ready' | 'unavailable';
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "Label".
 */
export type Label = string;
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "BackendState".
 */
export type BackendState =
  'unconfigured' | 'disconnected' | 'connected' | 'revoked' | 'unavailable';
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "Generation".
 */
export type Generation = string;
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "Nothing".
 */
export type Nothing = null;
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "BackendError".
 */
export type BackendError =
  | 'authentication_failed'
  | 'authentication_timeout'
  | 'incompatible_version'
  | 'invalid_message'
  | 'message_too_large'
  | 'unexpected_message'
  | 'stale_generation'
  | 'heartbeat_timeout'
  | 'session_replaced'
  | 'disconnected'
  | 'storage_unavailable'
  | 'server_busy';

export interface ApplicationStatus {
  status: Readiness;
  database: DatabaseStatus;
  backend: BackendStatus;
  version: Label;
  commit: Label;
}
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "DatabaseStatus".
 */
export interface DatabaseStatus {
  status: Readiness;
  engine: 'sqlite';
  version: Label;
}
/**
 * This interface was referenced by `ApplicationStatus`'s JSON-Schema
 * via the `definition` "BackendStatus".
 */
export interface BackendStatus {
  kind: 'thunderbird';
  status: BackendState;
  generation: Generation | Nothing;
  last_error: BackendError | Nothing;
  heartbeat_count: number;
}
