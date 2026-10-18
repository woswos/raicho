import { createStatusPoller } from './status_poller.js';
import { createStatusView } from './status_view.js';

const view = createStatusView();
let poller = createStatusPoller(view);

view.refreshButton.addEventListener('click', () => void poller.refresh());
window.addEventListener('pagehide', () => poller.stop());
window.addEventListener('pageshow', (event) => {
  if (!event.persisted) return;
  poller = createStatusPoller(view);
  void poller.refresh();
});
void poller.refresh();
