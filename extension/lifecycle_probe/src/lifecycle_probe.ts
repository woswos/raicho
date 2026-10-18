import type { Configuration } from './configuration.js';

interface Metadata {
  extension_version: string;
  browser_version: string;
  session_id: string;
}

interface Dependencies {
  connect: (endpoint: string) => WebSocket;
  schedule: (callback: () => void, delay: number) => number;
  cancel: (identifier: number) => void;
  random: () => number;
}

const browserDependencies: Dependencies = {
  connect: (endpoint) => new WebSocket(endpoint),
  schedule: (callback, delay) => globalThis.setTimeout(callback, delay),
  cancel: (identifier) => globalThis.clearTimeout(identifier),
  random: () => Math.random(),
};

export function startLifecycleProbe(
  configuration: Configuration,
  metadata: Metadata,
  dependencies: Dependencies = browserDependencies,
): () => void {
  let socket: WebSocket | undefined;
  let timer: number | undefined;
  let stopped = false;
  let failures = 0;
  let sequence = 0;

  function clearTimer() {
    if (timer !== undefined) dependencies.cancel(timer);
    timer = undefined;
  }

  function detachSocket() {
    if (!socket) return;
    socket.onopen = null;
    socket.onclose = null;
    socket.onerror = null;
    socket.close();
    socket = undefined;
  }

  function stop() {
    stopped = true;
    clearTimer();
    detachSocket();
  }

  function retry() {
    clearTimer();
    detachSocket();
    if (stopped) return;
    const delay = Math.min(
      30000,
      1000 * 2 ** Math.min(failures++, 5) * (1 + dependencies.random()),
    );
    timer = dependencies.schedule(connect, delay);
  }

  function transmit(initial: boolean) {
    if (!socket || socket.readyState !== 1 || socket.bufferedAmount > 4096) {
      retry();
      return;
    }
    try {
      socket.send(
        JSON.stringify({
          ...metadata,
          type: initial ? 'lifecycle_probe' : 'lifecycle_heartbeat',
          ...(initial ? { token: configuration.token } : {}),
          sequence: sequence++,
        }),
      );
      if (!initial) failures = 0;
      timer = dependencies.schedule(() => transmit(false), 10000);
    } catch {
      retry();
    }
  }

  function connect() {
    clearTimer();
    if (stopped) return;
    try {
      socket = dependencies.connect(configuration.endpoint);
      socket.onopen = () => {
        clearTimer();
        sequence = 0;
        transmit(true);
      };
      socket.onclose = (event) => {
        if (event.code >= 4000 && event.code < 5000) stop();
        else retry();
      };
      socket.onerror = retry;
      timer = dependencies.schedule(retry, 5000);
    } catch {
      retry();
    }
  }

  connect();
  return stop;
}
