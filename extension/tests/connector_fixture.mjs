import { resolve } from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';
import { probeFixture } from './probe_fixture.mjs';

export const { startConnectorTransport } = await import(
  pathToFileURL(
    resolve(
      process.env.RAICHO_EXTENSION_BUILD_DIR,
      'extension/src/connector_transport.js',
    ),
  ).href
);
export const configuration = {
  endpoint: 'ws://connector-proxy:8081/connector/v1',
  token: 'a'.repeat(64),
};
export const metadata = {
  backendVersion: '153.5.0',
  connectorVersion: '0.2.0',
};
export const generation = 'b'.repeat(32);
export const welcome = {
  type: 'welcome',
  protocol_version: 1,
  generation,
  capabilities: [],
  heartbeat_interval_ms: 15000,
  heartbeat_timeout_ms: 45000,
};
export const ping = {
  type: 'ping',
  protocol_version: 1,
  generation,
  sequence: 1,
};

export function connectorFixture() {
  const fixture = probeFixture();
  const connect = fixture.dependencies.connect;
  fixture.dependencies.connect = (endpoint) => {
    const socket = connect(endpoint);
    socket.receive = (data) =>
      socket.onmessage?.({
        data:
          typeof data === 'object' && !(data instanceof Uint8Array)
            ? JSON.stringify(data)
            : data,
      });
    return socket;
  };
  fixture.stop = startConnectorTransport(
    configuration,
    metadata,
    fixture.dependencies,
  );
  return fixture;
}
