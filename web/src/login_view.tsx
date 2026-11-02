import { useState } from 'preact/hooks';

import { apiRequest } from './api.js';
import type { SessionDocument } from './api_generated.js';
import { failureMessage } from './failures.js';

export function LoginView({ onSignedIn }: { onSignedIn: () => void }) {
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | undefined>();

  async function submit(event: Event) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setMessage(undefined);
    const result = await apiRequest<SessionDocument>('/api/session', { method: 'POST', body: { password } });
    setPending(false);
    if (result.ok) {
      setPassword('');
      onSignedIn();
    } else {
      setMessage(failureMessage(result.failure));
    }
  }

  return (
    <main id="main" class="login">
      <section class="login-card" aria-labelledby="login-title">
        <p class="eyebrow">Your Thunderbird, anywhere.</p>
        <h1 id="login-title">Sign in to Raicho</h1>
        <p class="muted">Your mail stays in Thunderbird. Raicho shows what Thunderbird has synchronized.</p>
        <form onSubmit={(event) => void submit(event)}>
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            autocomplete="current-password"
            required
            value={password}
            disabled={pending}
            onInput={(event) => setPassword(event.currentTarget.value)}
          />
          {message && (
            <p class="form-error" role="alert">
              {message}
            </p>
          )}
          <button type="submit" class="primary" disabled={pending}>
            {pending ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
