export function mockBrowser() {
  const originalValues = new Map(
    ['window', 'document', 'fetch'].map((name) => [name, Object.getOwnPropertyDescriptor(globalThis, name)]),
  );
  const timers = new Map();
  const listeners = new Map();
  const requests = [];
  let nextTimer = 0;
  const document = {
    hidden: false,
    addEventListener: (name, listener) => listeners.set(name, listener),
    removeEventListener: (name) => listeners.delete(name),
  };
  globalThis.document = document;
  globalThis.window = {
    setTimeout(callback, delay) {
      nextTimer += 1;
      timers.set(nextTimer, { callback, delay });
      return nextTimer;
    },
    clearTimeout: (timer) => timers.delete(timer),
  };
  globalThis.fetch = (url, options) =>
    new Promise((resolve, reject) => {
      requests.push({ url, options, resolve });
      options.signal.addEventListener('abort', () => reject(new Error('aborted')));
    });

  function setHidden(hidden) {
    document.hidden = hidden;
    listeners.get('visibilitychange')?.();
  }

  function fireTimer(delay) {
    for (const [identifier, timer] of timers) {
      if (timer.delay !== delay) continue;
      timers.delete(identifier);
      timer.callback();
      return;
    }
    throw new Error(`No pending ${String(delay)} ms timer`);
  }

  function restore() {
    for (const [name, descriptor] of originalValues) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor);
      else delete globalThis[name];
    }
  }

  return { requests, timers, setHidden, fireTimer, restore };
}
