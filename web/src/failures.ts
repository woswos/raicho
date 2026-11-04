import type { Failure } from './api.js';

export type FailureState = 'unauthenticated' | 'stale' | 'disconnected' | 'error';

/** How the interface should react to a failed request. */
export function failureState(failure: Failure): FailureState {
  if (failure.kind !== 'api') return 'error';
  switch (failure.code) {
    case 'unauthenticated':
      return 'unauthenticated';
    case 'stale_handle':
    case 'stale_cursor':
      return 'stale';
    case 'backend_disconnected':
      return 'disconnected';
    default:
      return 'error';
  }
}

export function failureMessage(failure: Failure): string {
  if (failure.kind === 'network') return 'Raicho could not be reached. Check that it is running, then try again.';
  if (failure.kind === 'timeout') return 'Raicho took too long to respond. Try again.';
  if (failure.kind === 'invalid') return 'Raicho returned an unexpected response.';
  switch (failure.code) {
    case 'invalid_password':
      return 'That password is not correct.';
    case 'rate_limited':
      return 'Too many attempts. Wait a minute, then try again.';
    case 'login_unconfigured':
      return 'No password is set. Run make deploy-login-init on the Raicho host.';
    case 'forbidden_origin':
      return 'Open Raicho at its configured address to sign in.';
    case 'unauthenticated':
      return 'Your session ended. Sign in again.';
    case 'stale_handle':
      return 'This mailbox changed in Thunderbird. Reload the mailboxes.';
    case 'stale_cursor':
      return 'This message list changed. Reload the mailbox.';
    case 'backend_disconnected':
      return 'Thunderbird is not connected. Mail is unavailable until it reconnects.';
    case 'backend_busy':
      return 'Thunderbird is busy. Try again shortly.';
    case 'backend_timeout':
      return 'Thunderbird took too long to answer. Try again.';
    case 'unsupported':
      return 'Thunderbird does not support this here.';
    case 'storage_unavailable':
      return 'Raicho could not reach its application database.';
    case 'invalid_request':
    case 'backend_failed':
      return 'Thunderbird could not complete the request.';
  }
}
