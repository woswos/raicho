import type { Configuration } from './configuration.js';
import { connectorSession, type Metadata } from './connector_session.js';
import { LIMITS } from '../../protocol/typescript/src/limits_generated.js';

const INITIAL_RETRY_DELAY_MS = 1000;
const MAXIMUM_RETRY_DELAY_MS = 30000;
const MAXIMUM_BACKOFF_EXPONENT = 5;

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
      MAXIMUM_RETRY_DELAY_MS,
      INITIAL_RETRY_DELAY_MS *
        2 ** Math.min(failures++, MAXIMUM_BACKOFF_EXPONENT) *
        (1 + dependencies.random()),
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
          current.readyState !== WebSocket.OPEN ||
          current.bufferedAmount !== 0 ||
          message.length > LIMITS.maximum_control_bytes
        ) {
          throw new Error('Connector sender is unavailable.');
        }
        current.send(message);
      };
      const handle = async (data: unknown) => {
        let received;
        try {
          received = await session.receive(data);
        } catch {
          if (active()) retry();
          return;
        }
        if (!active()) return;
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
          deadline(
            received.action === 'authenticate'
              ? LIMITS.authentication_deadline_ms
              : LIMITS.heartbeat_timeout_ms,
          );
        } catch {
          retry();
        }
      };
      let processing = Promise.resolve();
      current.onmessage = (event) => {
        processing = processing.then(() =>
          active() ? handle(event.data) : undefined,
        );
        return processing;
      };
      current.onclose = () => {
        if (active()) retry();
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
