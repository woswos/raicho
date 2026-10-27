import type { ConnectorMessage } from './contract_generated.js';
import type { ContractErrorCode } from './diagnostics_generated.js';
import { LIMITS } from './limits_generated.js';
import { isUnambiguousJson } from './raw_json.js';
import validate from './validator_generated.js';

const encoder = new TextEncoder();

export type Phase = 'authentication' | 'challenge' | 'handshake' | 'client_control' | 'server_control';

export class ContractError extends Error {
  constructor(readonly code: ContractErrorCode) {
    super(`Connector message rejected: ${code}.`);
    this.name = 'ContractError';
  }
}

function hasValidWireValues(value: unknown): boolean {
  const pending: unknown[] = [value];
  while (pending.length !== 0) {
    const current = pending.pop();
    if (typeof current === 'string') {
      if (/[^\x20-\x7e]/u.test(current)) return false;
    } else if (typeof current === 'number') {
      if (!Number.isFinite(current)) return false;
    } else if (current !== null && typeof current === 'object') {
      for (const [key, child] of Object.entries(current)) {
        if (/[^\x20-\x7e]/u.test(key)) return false;
        pending.push(child);
      }
    }
  }
  return true;
}

function decodeJson(raw: string): unknown {
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    throw new ContractError('invalid_message');
  }
}

function hasUnsupportedVersion(value: unknown): boolean {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    return false;
  }
  const version = (value as Record<string, unknown>).protocol_version;
  return (
    typeof version === 'number' &&
    Number.isInteger(version) &&
    version > 0 &&
    version <= LIMITS.maximum_wire_integer &&
    version !== LIMITS.protocol_version
  );
}

function checkPhase(message: ConnectorMessage, phase: Phase, generation: string | undefined): void {
  const accepted = {
    authentication: ['authenticate'],
    challenge: ['challenge', 'error'],
    handshake: ['welcome', 'error'],
    client_control: ['pong'],
    server_control: ['ping', 'error'],
  };
  if (!accepted[phase].includes(message.type)) {
    throw new ContractError('unexpected_message');
  }
  if ((phase === 'challenge' || phase === 'handshake') && message.type === 'error') {
    if (message.generation !== undefined || message.mac !== undefined) {
      throw new ContractError('unexpected_message');
    }
  } else if (phase === 'client_control' || phase === 'server_control') {
    if (generation === undefined || !('generation' in message) || message.generation !== generation) {
      throw new ContractError('stale_generation');
    }
    if (!('mac' in message) || message.mac === undefined) {
      throw new ContractError('invalid_message');
    }
  }
}

export function decodeFrame(raw: string, phase: Phase, generation?: string): ConnectorMessage {
  const maximumBytes = phase === 'authentication' ? LIMITS.maximum_authentication_bytes : LIMITS.maximum_control_bytes;
  // UTF-8 is never shorter than UTF-16, so oversized input fails before it is encoded.
  if (raw.length > maximumBytes || encoder.encode(raw).byteLength > maximumBytes) {
    throw new ContractError('message_too_large');
  }
  const message = decodeJson(raw);
  if (!isUnambiguousJson(raw, LIMITS.maximum_json_depth) || !hasValidWireValues(message)) {
    throw new ContractError('invalid_message');
  }
  if (hasUnsupportedVersion(message)) {
    throw new ContractError('incompatible_version');
  }
  if (!validate(message)) {
    throw new ContractError('invalid_message');
  }
  checkPhase(message, phase, generation);
  return message;
}
