import { parseConfiguration } from './configuration.js';
import { startLifecycleProbe } from './lifecycle_probe.js';

declare const messenger: {
  storage: { managed: { get: () => Promise<unknown> } };
  runtime: {
    getBrowserInfo: () => Promise<{ version: string }>;
    getManifest: () => { version: string };
  };
};

async function start() {
  const configuration = parseConfiguration(
    await messenger.storage.managed.get(),
  );
  if (!configuration) return;
  const browser = await messenger.runtime.getBrowserInfo();
  startLifecycleProbe(configuration, {
    extension_version: messenger.runtime.getManifest().version,
    browser_version: browser.version,
    session_id: crypto.randomUUID(),
  });
}

void start().catch(() => {
  console.error('Raicho connector configuration could not be loaded.');
});
