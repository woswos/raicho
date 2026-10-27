export function probeFixture() {
  const sockets = [];
  const timers = new Map();
  let timerIdentifier = 0;
  const dependencies = {
    connect(endpoint) {
      const socket = {
        endpoint,
        readyState: 0,
        bufferedAmount: 0,
        sent: [],
        close() {
          this.readyState = 3;
          this.onclose?.({ code: 1006 });
        },
        send(message) {
          this.sent.push(JSON.parse(message));
        },
        open() {
          this.readyState = 1;
          this.onopen?.();
        },
      };
      sockets.push(socket);
      return socket;
    },
    schedule(callback, delay) {
      timers.set(++timerIdentifier, { callback, delay });
      return timerIdentifier;
    },
    cancel(identifier) {
      timers.delete(identifier);
    },
    random: () => 0,
  };
  return {
    dependencies,
    sockets,
    timers,
    fireTimer(delay) {
      const [identifier, timer] = [...timers].find(
        ([, candidate]) => candidate.delay === delay,
      );
      timers.delete(identifier);
      timer.callback();
    },
  };
}
