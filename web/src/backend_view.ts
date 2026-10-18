import type { BackendStatus } from './status.js';

const descriptions = {
  unconfigured: [
    'Not configured',
    'The Thunderbird connection has not been set up yet.',
  ],
  disconnected: [
    'Disconnected',
    'Raicho is waiting for Thunderbird to connect.',
  ],
  connected: [
    'Connected',
    'Thunderbird is connected. Mail is not available in this interface yet.',
  ],
  revoked: [
    'Access revoked',
    'The connector credential was revoked. A new credential is required to restore access.',
  ],
  unavailable: [
    'Unavailable',
    'Connection status is unavailable. Check that Raicho can access its application database.',
  ],
} as const;

const protocolFailure =
  'The connection stopped after unexpected data. Check that Raicho and the Thunderbird connector are compatible.';
const errors: Record<NonNullable<BackendStatus['last_error']>, string> = {
  authentication_failed:
    'Thunderbird’s connection was rejected. Check its connector credential.',
  authentication_timeout:
    'Thunderbird did not complete authentication in time. Restart Thunderbird to try again.',
  incompatible_version:
    'Raicho and the Thunderbird connector use incompatible versions. Update them together.',
  invalid_message: protocolFailure,
  message_too_large: protocolFailure,
  unexpected_message: protocolFailure,
  stale_generation: protocolFailure,
  heartbeat_timeout:
    'Thunderbird stopped responding. Raicho is waiting for it to reconnect.',
  disconnected:
    'The Thunderbird connection was interrupted. Raicho is waiting for it to reconnect.',
  storage_unavailable:
    'Raicho could not check the connector credential. Check its application database.',
  server_busy:
    'Raicho is waiting for a connection attempt to finish. Thunderbird will retry.',
};

export function describeBackend(backend: BackendStatus) {
  const [label, description] = descriptions[backend.status];
  return {
    label,
    description:
      backend.status === 'disconnected' && backend.last_error !== null
        ? errors[backend.last_error]
        : description,
    state:
      backend.status === 'connected'
        ? 'ready'
        : backend.status === 'revoked' || backend.status === 'unavailable'
          ? 'error'
          : 'waiting',
  };
}
