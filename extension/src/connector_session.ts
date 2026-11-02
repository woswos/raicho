import type { Configuration } from './configuration.js';
import {
  authenticationMessage,
  clientProof,
  randomNonce,
  serverKey,
  verifyServerSignature,
  type AuthenticationFields,
} from '../../protocol/typescript/src/authentication.js';
import { createChannel, sessionKey, type Channel } from '../../protocol/typescript/src/channel.js';
import type { Authenticate, Operation, Outcome, Welcome } from '../../protocol/typescript/src/contract_generated.js';
import { decodeFrame } from '../../protocol/typescript/src/decode_frame.js';
import { LIMITS } from '../../protocol/typescript/src/limits_generated.js';

export interface Metadata {
  backendVersion: string;
  connectorVersion: string;
}

interface Received {
  action: 'authenticate' | 'welcome' | 'heartbeat' | 'request' | 'cancel' | 'retry' | 'stop';
  // A handshake reply is final, while a control reply is sealed when it is sent.
  reply?: string;
  control?: object;
  requestId?: number;
  operation?: Operation;
}

export function connectorSession(configuration: Configuration, metadata: Metadata) {
  let transcript: string | undefined;
  let session: { generation: string; channel: Channel } | undefined;
  let previousSequence = 0;

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

  async function accept(welcome: Welcome): Promise<Received> {
    if (
      transcript === undefined ||
      !(await verifyServerSignature(configuration.token, transcript, welcome.server_signature))
    ) {
      throw new Error('The server did not prove the connector token.');
    }
    const key = await sessionKey(await serverKey(configuration.token), transcript, welcome.generation);
    session = {
      generation: welcome.generation,
      channel: createChannel(key, 'client'),
    };
    return { action: 'welcome' };
  }

  async function control(raw: string, current: { generation: string; channel: Channel }): Promise<Received> {
    const message = await current.channel.open(raw, 'server_control', current.generation);
    // Only an authenticated frame can stop retries, and only for a newer connector.
    if (message.type === 'error') {
      return { action: message.code === 'session_replaced' ? 'stop' : 'retry' };
    }
    if (message.type === 'request') {
      return { action: 'request', requestId: message.request_id, operation: message.operation };
    }
    if (message.type === 'cancel') {
      return { action: 'cancel', requestId: message.request_id };
    }
    if (message.type !== 'ping' || message.sequence <= previousSequence) {
      throw new Error('Unexpected heartbeat sequence.');
    }
    previousSequence = message.sequence;
    return {
      action: 'heartbeat',
      control: {
        type: 'pong',
        protocol_version: message.protocol_version,
        generation: message.generation,
        sequence: message.sequence,
      },
    };
  }

  return {
    reply(requestId: number, result: Outcome): object {
      if (session === undefined) throw new Error('The session has not started.');
      return {
        type: 'reply',
        protocol_version: LIMITS.protocol_version,
        generation: session.generation,
        request_id: requestId,
        result,
      };
    },
    seal(message: object): Promise<string> {
      if (session === undefined) throw new Error('The session has not started.');
      return session.channel.seal(message);
    },
    async receive(raw: unknown): Promise<Received> {
      if (typeof raw !== 'string') throw new Error('Expected a text frame.');
      if (session !== undefined) return control(raw, session);
      const message = decodeFrame(raw, transcript === undefined ? 'challenge' : 'handshake');
      if (message.type === 'challenge') return answer(message.server_nonce);
      if (message.type === 'welcome') return accept(message);
      return { action: 'retry' };
    },
  };
}
