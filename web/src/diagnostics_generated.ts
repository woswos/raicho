// Generated from protocol/diagnostics.json.
export const BACKEND_STATES = [
  'unconfigured',
  'disconnected',
  'connected',
  'revoked',
  'unavailable',
] as const;
export const BACKEND_ERRORS = [
  'authentication_failed',
  'authentication_timeout',
  'incompatible_version',
  'invalid_message',
  'message_too_large',
  'unexpected_message',
  'stale_generation',
  'heartbeat_timeout',
  'session_replaced',
  'disconnected',
  'storage_unavailable',
  'server_busy',
] as const;
