// Generated from protocol/diagnostics.json.
export const CONTRACT_ERRORS = [
  'authentication_failed',
  'invalid_message',
  'message_too_large',
  'incompatible_version',
  'unexpected_message',
  'stale_generation',
] as const;
export type ContractErrorCode = (typeof CONTRACT_ERRORS)[number];
