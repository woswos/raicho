import type { Configuration } from './configuration.js';
import type { Authenticate, Pong } from './contract/contract_generated.js';
import { decodeFrame } from './contract/decode_frame.js';
import { LIMITS } from './contract/limits_generated.js';

export interface Metadata {
  backendVersion: string;
  connectorVersion: string;
}

interface Received {
  action: 'welcome' | 'heartbeat' | 'retry' | 'stop';
  reply?: string;
}

export function connectorSession(
  configuration: Configuration,
  metadata: Metadata,
) {
  let generation: string | undefined;
  let previousSequence = -1;
  const authentication: Authenticate = {
    type: 'authenticate',
    protocol_version: LIMITS.protocol_version,
    token: configuration.token,
    backend_kind: 'thunderbird',
    backend_version: metadata.backendVersion,
    connector_version: metadata.connectorVersion,
    capabilities: [],
  };

  return {
    authenticate(): string {
      const raw = JSON.stringify(authentication);
      decodeFrame(raw, 'authentication');
      return raw;
    },
    receive(raw: unknown): Received {
      if (typeof raw !== 'string') throw new Error('Expected a text frame.');
      const message = decodeFrame(
        raw,
        generation === undefined ? 'handshake' : 'server_control',
        generation,
      );
      if (message.type === 'error') {
        return {
          action: ['server_busy', 'heartbeat_timeout'].includes(message.code)
            ? 'retry'
            : 'stop',
        };
      }
      if (message.type === 'welcome') {
        generation = message.generation;
        return { action: 'welcome' };
      }
      if (message.type !== 'ping' || message.sequence <= previousSequence) {
        throw new Error('Unexpected heartbeat sequence.');
      }
      previousSequence = message.sequence;
      const reply: Pong = { ...message, type: 'pong' };
      return { action: 'heartbeat', reply: JSON.stringify(reply) };
    },
  };
}
