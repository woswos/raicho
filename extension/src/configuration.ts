export interface Configuration {
  endpoint: string;
  token: string;
}

const MAXIMUM_ENDPOINT_LENGTH = 2048;

function plainCharacters(endpoint: string): boolean {
  return [...endpoint].every((character) => {
    const code = character.charCodeAt(0);
    return code >= 32 && code !== 127 && !/\s/u.test(character);
  });
}

function validEndpoint(endpoint: string): boolean {
  if (
    endpoint.length > MAXIMUM_ENDPOINT_LENGTH ||
    !plainCharacters(endpoint) ||
    endpoint.includes('?') ||
    endpoint.includes('#') ||
    !/^wss?:\/\/[^/@]/iu.test(endpoint)
  ) {
    return false;
  }
  let address: URL;
  try {
    address = new URL(endpoint);
  } catch {
    return false;
  }
  return (
    ['ws:', 'wss:'].includes(address.protocol) &&
    address.hostname !== '' &&
    !address.username &&
    !address.password &&
    address.port !== '0'
  );
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
    !/^[a-f0-9]{64}$/.test(token) ||
    !validEndpoint(endpoint)
  ) {
    throw invalid();
  }
  return { endpoint, token };
}
