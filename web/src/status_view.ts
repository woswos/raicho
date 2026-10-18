import type { ApplicationStatus } from './status.js';

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

  function finish(state: string, message: string) {
    summary.dataset['state'] = state;
    summaryText.textContent = message;
    refreshButton.setAttribute('aria-disabled', 'false');
    refreshButton.textContent = 'Refresh status';
    if (announcement.textContent !== message)
      announcement.textContent = message;
  }

  function onLoading() {
    refreshButton.setAttribute('aria-disabled', 'true');
    refreshButton.textContent = 'Checking…';
  }

  function onStatus(status: ApplicationStatus) {
    finish('ready', 'Raicho is ready');
    serverStatus.textContent = 'Ready';
    serverStatus.dataset['state'] = 'ready';
    databaseStatus.textContent = 'Ready';
    databaseVersion.textContent = `SQLite ${status.database.version}`;
    applicationVersion.textContent =
      status.commit === 'unknown'
        ? status.version
        : `${status.version} (${status.commit})`;
    backendStatus.textContent = 'Not configured';
    backendDescription.textContent =
      'The Thunderbird connection is not configured yet. Mail is not available in this interface.';
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
    backendDescription.textContent =
      'Connection details are unavailable until Raicho responds.';
    lastChecked.textContent = 'The latest status check did not succeed.';
  }

  return { onLoading, onStatus, onError, refreshButton };
}
