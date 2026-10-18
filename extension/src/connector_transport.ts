import type { Configuration } from './configuration.js';
import { connectorSession, type Metadata } from './connector_session.js';
import { LIMITS } from './contract/limits_generated.js';

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

export function startConnectorTransport(
  configuration: Configuration,
  metadata: Metadata,
  dependencies: Dependencies = browserDependencies,
): () => void {
  let socket: WebSocket | undefined;
  let timer: number | undefined;
  let stopped = false;
  let failures = 0;

  function clearTimer() {
    if (timer !== undefined) dependencies.cancel(timer);
    timer = undefined;
  }

  function detachSocket() {
    const previous = socket;
    socket = undefined;
    if (!previous) return;
    previous.onopen = null;
    previous.onclose = null;
    previous.onerror = null;
    previous.onmessage = null;
    previous.close();
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

  function connect() {
    clearTimer();
    if (stopped) return;
    try {
      const current = dependencies.connect(configuration.endpoint);
      socket = current;
      const session = connectorSession(configuration, metadata);
      const active = () => !stopped && current === socket;
      const deadline = (delay: number) => {
        clearTimer();
        timer = dependencies.schedule(() => {
          if (active()) retry();
        }, delay);
      };
      const send = (message: string) => {
        if (
          current.readyState !== 1 ||
          current.bufferedAmount !== 0 ||
          message.length > LIMITS.control_max_bytes
        ) {
          throw new Error('Connector sender is unavailable.');
        }
        current.send(message);
      };
      current.onopen = () => {
        if (!active()) return;
        let authentication: string;
        try {
          authentication = session.authenticate();
        } catch {
          stop();
          return;
        }
        try {
          send(authentication);
          deadline(LIMITS.authentication_deadline_ms);
        } catch {
          retry();
        }
      };
      current.onmessage = (event) => {
        if (!active()) return;
        let received;
        try {
          received = session.receive(event.data);
        } catch {
          stop();
          return;
        }
        if (received.action === 'stop') {
          stop();
          return;
        }
        if (received.action === 'retry') {
          retry();
          return;
        }
        try {
          if (received.reply !== undefined) send(received.reply);
          if (received.action === 'heartbeat') failures = 0;
          deadline(LIMITS.heartbeat_timeout_ms);
        } catch {
          retry();
        }
      };
      current.onclose = (event) => {
        if (!active()) return;
        if ([4001, 4002, 4003].includes(event.code)) stop();
        else retry();
      };
      current.onerror = () => {
        if (active()) retry();
      };
      deadline(LIMITS.authentication_deadline_ms);
    } catch {
      retry();
    }
  }

  connect();
  return stop;
}
