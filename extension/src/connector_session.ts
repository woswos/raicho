import type { Configuration } from './configuration.js';
import {
  authenticationMessage,
  clientProof,
  randomNonce,
  serverSignature,
  type AuthenticationFields,
} from '../../protocol/typescript/src/authentication.js';
import type {
  Authenticate,
  Pong,
} from '../../protocol/typescript/src/contract_generated.js';
import { decodeFrame } from '../../protocol/typescript/src/decode_frame.js';
import { LIMITS } from '../../protocol/typescript/src/limits_generated.js';

export interface Metadata {
  backendVersion: string;
  connectorVersion: string;
}

interface Received {
  action: 'authenticate' | 'welcome' | 'heartbeat' | 'retry' | 'stop';
  reply?: string;
}

export function connectorSession(
  configuration: Configuration,
  metadata: Metadata,
) {
  let transcript: string | undefined;
  let generation: string | undefined;
  let previousSequence = -1;

  async function answer(serverNonce: string): Promise<Received> {
    const fields: AuthenticationFields = {
      protocol_version: LIMITS.protocol_version,
      backend_kind: 'thunderbird',
      backend_version: metadata.backendVersion,
      connector_version: metadata.connectorVersion,
      capabilities: [],
      client_nonce: randomNonce(),
    };
    transcript = authenticationMessage(serverNonce, fields);
    const authentication: Authenticate = {
      type: 'authenticate',
      ...fields,
      client_proof: await clientProof(configuration.token, transcript),
    };
    const reply = JSON.stringify(authentication);
    decodeFrame(reply, 'authentication');
    return { action: 'authenticate', reply };
  }

  return {
    // Until the server proves it knows the token, its errors and closes may be spoofed.
    get proven() {
      return generation !== undefined;
    },
    async receive(raw: unknown): Promise<Received> {
      if (typeof raw !== 'string') throw new Error('Expected a text frame.');
      const phase =
        generation !== undefined
          ? 'server_control'
          : transcript === undefined
            ? 'challenge'
            : 'handshake';
      const message = decodeFrame(raw, phase, generation);
      if (message.type === 'error') {
        return {
          action:
            generation === undefined ||
            ['server_busy', 'heartbeat_timeout'].includes(message.code)
              ? 'retry'
              : 'stop',
        };
      }
      if (message.type === 'challenge') return answer(message.server_nonce);
      if (message.type === 'welcome') {
        if (
          transcript === undefined ||
          message.server_signature !==
            (await serverSignature(configuration.token, transcript))
        ) {
          throw new Error('The server did not prove the connector token.');
        }
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
