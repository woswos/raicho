import {
  readStatus,
  StatusResponseError,
  type ApplicationStatus,
} from './status.js';

const UNAVAILABLE = 503;

export interface StatusHandlers {
  onLoading: () => void;
  onStatus: (status: ApplicationStatus) => void;
  onError: (message: string) => void;
}

export function createStatusPoller(handlers: StatusHandlers) {
  let pendingRequest: AbortController | undefined;
  let refreshTimer: number | undefined;
  let stopped = false;

  function clearRefreshTimer() {
    window.clearTimeout(refreshTimer);
    refreshTimer = undefined;
  }

  async function refresh() {
    if (stopped || document.hidden || pendingRequest) return;
    clearRefreshTimer();
    const controller = new AbortController();
    pendingRequest = controller;
    const timeout = window.setTimeout(() => controller.abort('timeout'), 8000);
    handlers.onLoading();

    try {
      const response = await fetch('/api/status', {
        cache: 'no-store',
        headers: { Accept: 'application/json' },
        signal: controller.signal,
      });
      let payload: unknown;
      try {
        payload = await response.json();
      } catch {
        payload = undefined;
      }
      const status =
        response.ok || response.status === UNAVAILABLE
          ? readStatus(payload)
          : undefined;
      if (status !== undefined) {
        handlers.onStatus(status);
      } else if (!response.ok) {
        handlers.onError(
          `Raicho could not provide its status (HTTP ${String(response.status)}).`,
        );
      } else {
        throw new StatusResponseError();
      }
    } catch (error: unknown) {
      if (controller.signal.reason === 'hidden' || stopped) return;
      const message =
        controller.signal.reason === 'timeout'
          ? 'Raicho took too long to respond. Try again.'
          : error instanceof StatusResponseError
            ? error.message
            : 'Raicho could not be reached. Check that it is running, then try again.';
      handlers.onError(message);
    } finally {
      window.clearTimeout(timeout);
      pendingRequest = undefined;
      if (!stopped && !document.hidden) {
        refreshTimer = window.setTimeout(() => void refresh(), 15000);
      }
    }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      clearRefreshTimer();
      pendingRequest?.abort('hidden');
    } else {
      void refresh();
    }
  }

  function stop() {
    stopped = true;
    clearRefreshTimer();
    pendingRequest?.abort('stopped');
    document.removeEventListener('visibilitychange', onVisibilityChange);
  }

  document.addEventListener('visibilitychange', onVisibilityChange);
  return { refresh, stop };
}
