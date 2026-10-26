import type { MailApi } from './mail_api.js';
import { parseConfiguration } from '../../extension/src/configuration.js';
import { dispatchCommand } from './dispatcher.js';
import { startProbeTransport } from './probe_transport.js';

declare const messenger: MailApi;

async function start() {
  const configuration = parseConfiguration(await messenger.storage.managed.get());
  if (!configuration) throw new Error('Mail API probe is not configured.');
  const browser = await messenger.runtime.getBrowserInfo();
  const metadata = {
    type: 'mail_probe',
    token: configuration.token,
    browser_version: browser.version,
    extension_version: messenger.runtime.getManifest().version,
    session_id: crypto.randomUUID(),
  };
  startProbeTransport(configuration.endpoint, metadata, (command) => dispatchCommand(messenger, command));
}

void start().catch(() => console.error('Mail API probe could not start.'));
