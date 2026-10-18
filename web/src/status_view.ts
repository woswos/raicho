import type { ApplicationStatus } from './status.js';
import { describeBackend } from './backend_view.js';

function element(id: string): HTMLElement {
  const result = document.getElementById(id);
  if (!result) throw new Error(`Missing diagnostic element: ${id}`);
  return result;
}

export function createStatusView() {
  const summary = element('summary');
  const summaryText = element('summary-text');
  const serverStatus = element('server-status');
  const databaseStatus = element('database-status');
  const databaseVersion = element('database-version');
  const applicationVersion = element('application-version');
  const backendStatus = element('backend-status');
  const backendDescription = element('backend-description');
  const lastChecked = element('last-checked');
  const announcement = element('announcement');
  const refreshControl = element('refresh');
  if (!(refreshControl instanceof HTMLButtonElement)) {
    throw new Error('Diagnostic refresh control is not a button.');
  }
  const refreshButton = refreshControl;

  function finish(state: string, message: string, announced = message) {
    summary.dataset['state'] = state;
    summaryText.textContent = message;
    refreshButton.setAttribute('aria-disabled', 'false');
    refreshButton.textContent = 'Refresh status';
    if (announcement.textContent !== announced)
      announcement.textContent = announced;
  }

  function onLoading() {
    refreshButton.setAttribute('aria-disabled', 'true');
    refreshButton.textContent = 'Checking…';
  }

  function onStatus(status: ApplicationStatus) {
    const backend = describeBackend(status.backend);
    finish(
      'ready',
      'Raicho is ready',
      `Raicho is ready. Thunderbird: ${backend.label}.`,
    );
    serverStatus.textContent = 'Ready';
    serverStatus.dataset['state'] = 'ready';
    databaseStatus.textContent = 'Ready';
    databaseVersion.textContent = `SQLite ${status.database.version}`;
    applicationVersion.textContent = status.version;
    backendStatus.textContent = backend.label;
    backendStatus.dataset['state'] = backend.state;
    backendDescription.textContent = backend.description;
    lastChecked.textContent = `Last checked at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
  }

  function onError(message: string) {
    finish('error', message);
    serverStatus.textContent = 'Unavailable';
    serverStatus.dataset['state'] = 'error';
    databaseStatus.textContent = 'Unknown';
    databaseVersion.textContent = 'Not available';
    applicationVersion.textContent = 'Not available';
    backendStatus.textContent = 'Not checked';
    backendStatus.dataset['state'] = 'waiting';
    backendDescription.textContent =
      'Connection details are unavailable until Raicho responds.';
    lastChecked.textContent = 'The latest status check did not succeed.';
  }

  return { onLoading, onStatus, onError, refreshButton };
}
