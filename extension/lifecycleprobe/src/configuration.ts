export interface Configuration {
  endpoint: string;
  token: string;
}

export function parseConfiguration(value: unknown): Configuration | undefined {
  const invalid = () =>
    new Error('Managed connector configuration is invalid.');
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw invalid();
  }
  const settings = value as Record<string, unknown>;
  const { endpoint, token } = settings;
  if (endpoint === undefined && token === undefined) return undefined;
  if (
    typeof endpoint !== 'string' ||
    typeof token !== 'string' ||
    !/^[a-f0-9]{64}$/.test(token)
  ) {
    throw invalid();
  }
  let address: URL;
  try {
    address = new URL(endpoint);
  } catch {
    throw invalid();
  }
  if (
    !['ws:', 'wss:'].includes(address.protocol) ||
    address.username ||
    address.password ||
    address.search ||
    address.hash
  ) {
    throw invalid();
  }
  return { endpoint, token };
}
