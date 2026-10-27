import { constantTimeEqual, hex, hmac, type Bytes } from './authentication.js';
import type { ConnectorMessage } from './contract_generated.js';
import { ContractError, decodeFrame, type Phase } from './decode_frame.js';

const SESSION_KEY_LABEL = 'raicho-connector-session';
const FRAME_LABEL = 'raicho-connector-frame';

export type Peer = 'server' | 'client';

export function sessionKey(serverKey: Bytes, transcript: string, generation: string): Promise<Bytes> {
  return hmac(serverKey, `${SESSION_KEY_LABEL}\n${transcript}\n${generation}`);
}

function canonicalValue(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalValue).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return canonicalObject(Object.entries(value));
  }
  return JSON.stringify(value);
}

function canonicalObject(entries: [string, unknown][]): string {
  const members = entries
    .filter(([, value]) => value !== undefined)
    .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
    .map(([name, value]) => `${JSON.stringify(name)}:${canonicalValue(value)}`);
  return `{${members.join(',')}}`;
}

export function canonicalJson(message: object): string {
  return canonicalObject(Object.entries(message).filter(([name]) => name !== 'mac'));
}

export async function frameMac(key: Bytes, sender: Peer, counter: number, message: object): Promise<string> {
  return hex(await hmac(key, `${FRAME_LABEL}\n${sender}\n${String(counter)}\n${canonicalJson(message)}`));
}

export function createChannel(key: Bytes, local: Peer) {
  const remote: Peer = local === 'server' ? 'client' : 'server';
  let sent = 0;
  let received = 0;
  let failed = false;
  return {
    async seal(message: object): Promise<string> {
      if (failed) throw new ContractError('authentication_failed');
      const mac = await frameMac(key, local, sent++, message);
      return JSON.stringify({ ...message, mac });
    },
    async open(raw: string, phase: Phase, generation: string): Promise<ConnectorMessage> {
      if (failed) throw new ContractError('authentication_failed');
      // Overlapping calls must each check the next counter, in the order frames arrived.
      const counter = received++;
      try {
        const message = decodeFrame(raw, phase, generation);
        const mac = 'mac' in message ? message.mac : undefined;
        if (mac === undefined) throw new ContractError('invalid_message');
        const expected = await frameMac(key, remote, counter, message);
        if (!constantTimeEqual(mac, expected)) {
          throw new ContractError('authentication_failed');
        }
        return message;
      } catch (error) {
        failed = true;
        throw error;
      }
    },
  };
}

export type Channel = ReturnType<typeof createChannel>;
