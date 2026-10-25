// Generated from protocol/schema/connector.schema.json.

export type ConnectorMessage =
  Challenge | Authenticate | Welcome | Ping | Pong | ProtocolError;
export type Nonce = string;
/**
 * @maxItems 0
 */
export type Capabilities = [];
export type Signature = string;
export type Generation = string;

export interface Challenge {
  type: 'challenge';
  protocol_version: 1;
  server_nonce: Nonce;
}
export interface Authenticate {
  type: 'authenticate';
  protocol_version: 1;
  backend_kind: string;
  backend_version: string;
  connector_version: string;
  capabilities: Capabilities;
  client_nonce: Nonce;
  client_proof: Signature;
}
export interface Welcome {
  type: 'welcome';
  protocol_version: 1;
  generation: Generation;
  capabilities: Capabilities;
  heartbeat_interval_ms: 15000;
  heartbeat_timeout_ms: 45000;
  server_signature: Signature;
}
export interface Ping {
  type: 'ping';
  protocol_version: 1;
  generation: Generation;
  sequence: number;
}
export interface Pong {
  type: 'pong';
  protocol_version: 1;
  generation: Generation;
  sequence: number;
}
export interface ProtocolError {
  type: 'error';
  protocol_version: 1;
  generation?: Generation;
  code:
    | 'authentication_failed'
    | 'incompatible_version'
    | 'invalid_message'
    | 'message_too_large'
    | 'unexpected_message'
    | 'stale_generation'
    | 'heartbeat_timeout'
    | 'session_replaced'
    | 'server_busy';
}
