import type { Configuration } from './configuration.js';
import { connectorSession, type Metadata } from './connector_session.js';
import type { MailAdapter } from './mail_adapter.js';
import type { Operation } from '../../protocol/typescript/src/contract_generated.js';
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
  adapter: Pick<MailAdapter, 'execute' | 'reset'>,
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
      INITIAL_RETRY_DELAY_MS * 2 ** Math.min(failures++, MAXIMUM_BACKOFF_EXPONENT) * (1 + dependencies.random()),
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
        // A reply may still be buffered, but a socket holding more than one frame has stalled.
        if (
          current.readyState !== WebSocket.OPEN ||
          current.bufferedAmount > LIMITS.maximum_control_bytes ||
          message.length > LIMITS.maximum_control_bytes
        ) {
          throw new Error('Connector sender is unavailable.');
        }
        current.send(message);
      };
      // Frame MACs count frames in order, so sealing and sending share one queue.
      let outgoing = Promise.resolve();
      const transmit = (message: object) => {
        outgoing = outgoing.then(async () => {
          if (!active()) return;
          try {
            send(await session.seal(message));
          } catch {
            if (active()) {
              console.warn('Raicho connector could not reply to the server and will reconnect.');
              retry();
            }
          }
        });
        return outgoing;
      };
      const cancelled = new Set<number>();
      const run = async (requestId: number, operation: Operation) => {
        const result = await adapter.execute(operation);
        if (cancelled.delete(requestId) || !active()) return;
        await transmit(session.reply(requestId, result));
      };
      const handle = async (data: unknown) => {
        let received;
        try {
          received = await session.receive(data);
        } catch {
          if (active()) {
            console.warn('Raicho connector rejected a message from the server and will reconnect.');
            retry();
          }
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
        if (received.action === 'welcome') adapter.reset();
        if (received.requestId !== undefined) {
          if (received.operation !== undefined) void run(received.requestId, received.operation);
          else cancelled.add(received.requestId);
        }
        try {
          if (received.reply !== undefined) send(received.reply);
          if (received.action === 'heartbeat') failures = 0;
          deadline(
            received.action === 'authenticate' ? LIMITS.authentication_deadline_ms : LIMITS.heartbeat_timeout_ms,
          );
        } catch {
          console.warn('Raicho connector could not reply to the server and will reconnect.');
          retry();
          return;
        }
        if (received.control !== undefined) await transmit(received.control);
      };
      let processing = Promise.resolve();
      current.onmessage = (event) => {
        processing = processing.then(() => (active() ? handle(event.data) : undefined));
        // WebSocket ignores the result, but tests await it to see each message handled.
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
      console.warn('Raicho connector could not open a connection and will retry.');
      retry();
    }
  }

  connect();
  return stop;
}
