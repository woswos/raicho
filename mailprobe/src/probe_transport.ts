import { CommandSession } from './command_session.js';
import type { Command } from './validation.js';

interface Dependencies {
  connect: (endpoint: string) => WebSocket;
  schedule: (callback: () => void, delay: number) => unknown;
}

export function startProbeTransport(
  endpoint: string,
  metadata: Record<string, string>,
  dispatch: (command: Command) => Promise<unknown>,
  dependencies: Dependencies = {
    connect: (address) => new WebSocket(address),
    schedule: (callback, delay) => setTimeout(callback, delay),
  },
) {
  const session = new CommandSession(dispatch);
  let stopped = false;
  function connect() {
    const socket = dependencies.connect(endpoint);
    socket.binaryType = 'arraybuffer';
    socket.onopen = () => socket.send(JSON.stringify(metadata));
    socket.onmessage = (event: MessageEvent<unknown>) => {
      void receive(event.data).catch(() =>
        socket.close(1003, 'Invalid fixture command.'),
      );
    };
    socket.onclose = (event) => {
      if (event.code === 4003) stopped = true;
      if (!stopped) dependencies.schedule(connect, 1000);
    };
    async function receive(data: unknown) {
      const text =
        data instanceof ArrayBuffer
          ? new TextDecoder('utf-8', { fatal: true }).decode(data)
          : typeof data === 'string'
            ? data
            : '';
      if (!text || new TextEncoder().encode(text).length > 65536)
        throw new Error('Invalid fixture frame.');
      const value: unknown = JSON.parse(text);
      const result = await session.execute(value);
      if (socket.readyState === WebSocket.OPEN)
        socket.send(JSON.stringify(result));
    }
  }
  connect();
}
