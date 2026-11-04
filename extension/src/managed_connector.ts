import { parseConfiguration, type Configuration } from './configuration.js';
import type { Metadata } from './connector_session.js';
import { startConnectorTransport } from './connector_transport.js';
import { createMailAdapter } from './mail_adapter.js';
import type { MailApi } from './mail_api.js';

export interface ManagedApi extends MailApi {
  storage: { managed: { get: () => Promise<unknown> } };
  runtime: {
    getBrowserInfo: () => Promise<{ version: string }>;
    getManifest: () => { version: string };
  };
}

export function startManagedConnector(
  api: ManagedApi,
  connect: (configuration: Configuration, metadata: Metadata) => () => void = (configuration, metadata) =>
    startConnectorTransport(configuration, metadata, createMailAdapter(api)),
): () => void {
  let stopped = false;
  let stopConnection: (() => void) | undefined;

  async function start() {
    try {
      const configuration = parseConfiguration(await api.storage.managed.get());
      if (stopped || !configuration) return;
      const browser = await api.runtime.getBrowserInfo();
      if (stopped) return;
      stopConnection = connect(configuration, {
        backendVersion: browser.version,
        connectorVersion: api.runtime.getManifest().version,
      });
    } catch {
      if (!stopped) {
        console.error('Raicho connector configuration could not be loaded.');
      }
    }
  }

  void start();
  return () => {
    stopped = true;
    stopConnection?.();
    stopConnection = undefined;
  };
}
