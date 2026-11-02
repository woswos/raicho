import { resolve } from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';
import { probeFixture } from './probe_fixture.mjs';

function built(path) {
  return import(pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, path)).href);
}

export const { startConnectorTransport } = await built('extension/src/connector_transport.js');
export const authentication = await built('protocol/typescript/src/authentication.js');
export const channel = await built('protocol/typescript/src/channel.js');
export const configuration = {
  endpoint: 'ws://connector-proxy:8081/connector/v1',
  token: 'a'.repeat(64),
};
export const metadata = {
  backendVersion: '153.5.0',
  connectorVersion: '0.2.0',
};
export const generation = 'b'.repeat(32);
export const challenge = {
  type: 'challenge',
  protocol_version: 2,
  server_nonce: 'f'.repeat(64),
};
export const welcome = {
  type: 'welcome',
  protocol_version: 2,
  generation,
  capabilities: [],
};
export const ping = {
  type: 'ping',
  protocol_version: 2,
  generation,
  sequence: 1,
};

function transcript(authenticate) {
  return authentication.authenticationMessage(challenge.server_nonce, authenticate);
}

export async function provenWelcome(authenticate, token = configuration.token) {
  return {
    ...welcome,
    server_signature: await authentication.serverSignature(token, transcript(authenticate)),
  };
}

export async function serverChannel(authenticate) {
  return channel.createChannel(
    await channel.sessionKey(await authentication.serverKey(configuration.token), transcript(authenticate), generation),
    'server',
  );
}

export function connectorFixture() {
  const fixture = probeFixture();
  const connect = fixture.dependencies.connect;
  fixture.dependencies.connect = (endpoint) => {
    const socket = connect(endpoint);
    socket.receive = (data) =>
      socket.onmessage?.({
        data: typeof data === 'object' && !(data instanceof Uint8Array) ? JSON.stringify(data) : data,
      });
    socket.handshake = async () => {
      socket.open();
      await socket.receive(challenge);
      const authenticate = socket.sent.at(-1);
      await socket.receive(await provenWelcome(authenticate));
      socket.server = await serverChannel(authenticate);
    };
    socket.receiveSealed = async (message) => socket.receive(await socket.server.seal(message));
    return socket;
  };
  fixture.requests = [];
  fixture.resets = 0;
  fixture.adapter = {
    execute: (operation) =>
      new Promise((resolve) => {
        fixture.requests.push({ operation, resolve });
      }),
    reset: () => {
      fixture.resets += 1;
    },
  };
  fixture.stop = startConnectorTransport(configuration, metadata, fixture.adapter, fixture.dependencies);
  return fixture;
}
