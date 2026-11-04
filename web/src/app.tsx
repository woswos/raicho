import { useEffect, useState } from 'preact/hooks';

import { apiRequest } from './api.js';
import type { PreferencesDocument, SessionDocument, Theme } from './api_generated.js';
import { describeBackend } from './backend_view.js';
import { LoginView } from './login_view.js';
import { MailView } from './mail_view.js';
import type { ApplicationStatus } from './status.js';
import { createStatusPoller } from './status_poller.js';

type Session = 'checking' | 'signed_out' | 'signed_in';

const THEMES: { value: Theme; label: string }[] = [
  { value: 'system', label: 'System theme' },
  { value: 'light', label: 'Light theme' },
  { value: 'dark', label: 'Dark theme' },
];

function applyTheme(theme: Theme) {
  if (theme === 'system') delete document.documentElement.dataset['theme'];
  else document.documentElement.dataset['theme'] = theme;
}

function Logo({ theme }: { theme: Theme }) {
  const image = (source: string) => <img class="logo" src={source} alt="Raicho" width={152} height={38} />;
  if (theme === 'light') return image('/assets/brand/logos/horizontal.svg');
  if (theme === 'dark') return image('/assets/brand/logos/horizontal-dark.svg');
  return (
    <picture>
      <source srcset="/assets/brand/logos/horizontal-dark.svg" media="(prefers-color-scheme: dark)" />
      {image('/assets/brand/logos/horizontal.svg')}
    </picture>
  );
}

export function App() {
  const [session, setSession] = useState<Session>('checking');
  const [theme, setTheme] = useState<Theme>('system');
  const [status, setStatus] = useState<ApplicationStatus | undefined>();
  const [statusError, setStatusError] = useState<string | undefined>();

  useEffect(() => {
    const poller = createStatusPoller({
      onLoading() {},
      onStatus(current) {
        setStatus(current);
        setStatusError(undefined);
      },
      onError: setStatusError,
    });
    void poller.refresh();
    return () => poller.stop();
  }, []);

  useEffect(() => {
    void apiRequest<SessionDocument>('/api/session').then((result) =>
      setSession(result.ok ? 'signed_in' : 'signed_out'),
    );
  }, []);

  useEffect(() => {
    if (session !== 'signed_in') return;
    void apiRequest<PreferencesDocument>('/api/preferences').then((result) => {
      if (result.ok && result.document) setTheme(result.document.theme);
    });
  }, [session]);

  useEffect(() => applyTheme(theme), [theme]);

  async function chooseTheme(next: Theme) {
    const previous = theme;
    setTheme(next);
    const result = await apiRequest<PreferencesDocument>('/api/preferences', { method: 'PUT', body: { theme: next } });
    if (!result.ok) setTheme(previous);
  }

  async function signOut() {
    await apiRequest('/api/session', { method: 'DELETE' });
    setSession('signed_out');
  }

  const backend = status ? describeBackend(status.backend) : undefined;
  const connection = statusError ?? (backend ? `Thunderbird: ${backend.label}` : 'Checking Thunderbird…');
  return (
    <div class="app-shell">
      <a class="skip-link" href="#main">
        Skip to content
      </a>
      <header class="site-header">
        <Logo theme={theme} />
        <div class="header-actions">
          <span class="status-pill" data-state={statusError ? 'error' : backend?.state} title={backend?.description}>
            {connection}
          </span>
          {session === 'signed_in' && (
            <>
              <label class="visually-hidden" for="theme">
                Theme
              </label>
              <select
                id="theme"
                value={theme}
                onChange={(event) => void chooseTheme(event.currentTarget.value as Theme)}
              >
                {THEMES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button type="button" class="secondary" onClick={() => void signOut()}>
                Sign out
              </button>
            </>
          )}
        </div>
      </header>
      {session === 'checking' && (
        <main id="main" class="placeholder">
          <p>Checking your session…</p>
        </main>
      )}
      {session === 'signed_out' && <LoginView onSignedIn={() => setSession('signed_in')} />}
      {session === 'signed_in' && (
        <MailView
          connected={status === undefined ? undefined : status.backend.status === 'connected'}
          onSignedOut={() => setSession('signed_out')}
        />
      )}
    </div>
  );
}
