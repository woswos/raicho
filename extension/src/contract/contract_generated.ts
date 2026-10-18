// Generated from protocol/schema/connector.schema.json.

export type ConnectorMessage =
  Authenticate | Welcome | Ping | Pong | ProtocolError;
/**
 * @maxItems 0
 */
export type Capabilities = [];
export type Generation = string;

export interface Authenticate {
  type: 'authenticate';
  protocol_version: 1;
  token: string;
  backend_kind: string;
  backend_version: string;
  connector_version: string;
  capabilities: Capabilities;
}
export interface Welcome {
  type: 'welcome';
  protocol_version: 1;
  generation: Generation;
  capabilities: Capabilities;
  heartbeat_interval_ms: 15000;
  heartbeat_timeout_ms: 45000;
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
