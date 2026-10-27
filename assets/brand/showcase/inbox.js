const app = document.getElementById('mail-app');
const messages = window.raichoMessages;
const list = document.getElementById('message-list');
const detail = document.getElementById('message-detail');
const search = document.getElementById('mail-search');
const themeToggle = document.getElementById('theme-toggle');
const densityToggle = document.getElementById('density-toggle');
const composer = document.getElementById('composer');
const folderNames = {
  inbox: 'All inboxes',
  starred: 'Starred',
  drafts: 'Drafts',
  sent: 'Sent',
  archive: 'Archive',
};
let activeFolder = 'inbox';
let selectedId = 'walk';
let statusTimer;
// Keep aligned with the reading-pane breakpoint in inbox_responsive.css.
const readingPaneLayout = window.matchMedia('(max-width: 900px)');
function searchableText(message) {
  return `${message.sender} ${message.subject} ${message.snippet} ${message.paragraphs.join(' ')}`
    .replace(/<[^>]*>/g, ' ')
    .toLowerCase();
}
function visibleMessages() {
  const query = search.value.trim().toLowerCase();
  return messages.filter(
    (message) =>
      (activeFolder === 'starred' ? message.starred : message.folder === activeFolder) &&
      searchableText(message).includes(query),
  );
}
function focusMessageRow() {
  const selected = list.querySelector('.selected');
  if (selected?.offsetParent) selected.focus();
}
function announce(message) {
  clearTimeout(statusTimer);
  document.getElementById('app-status').textContent = message;
  statusTimer = setTimeout(() => {
    document.getElementById('app-status').textContent = '';
  }, 3500);
}
function renderDetail(visible) {
  const message = visible.find((item) => item.id === selectedId);
  document.getElementById('reader-actions').hidden = !message;
  for (const id of ['archive-button', 'star-button']) document.getElementById(id).disabled = !message;
  document.getElementById('message-position').textContent = message
    ? `${visible.indexOf(message) + 1} of ${visible.length}`
    : '';
  if (!message) {
    detail.innerHTML =
      '<div class="empty-state"><strong>No message selected</strong>Choose a message to read it here.</div>';
    return;
  }
  document.getElementById('star-button').setAttribute('aria-pressed', String(message.starred));
  document.getElementById('archive-button').disabled = message.folder === 'archive';
  detail.innerHTML = `<div class="message-category"><span>${message.account}</span>${message.date}</div><h2 class="message-subject">${message.subject}</h2><div class="sender-block"><div class="sender-avatar">${message.initials}</div><div class="sender-info"><b>${message.sender}</b><span>&lt;${message.address}&gt;</span><small>to Alex · ${message.account === 'Work' ? 'alex@studio.example' : 'alex@example.com'}</small></div></div><div class="message-body">${message.paragraphs.map((paragraph) => `<p>${paragraph}</p>`).join('')}</div>${message.attachment ? `<div class="attachment"><svg class="icon" aria-hidden="true"><use href="#draft"/></svg><div>${message.attachment}<small>PDF document · ${message.size}</small></div></div>` : ''}`;
}
function renderMessages() {
  const focusWasInList = list.contains(document.activeElement);
  const visible = visibleMessages();
  if (!visible.some((message) => message.id === selectedId)) selectedId = visible[0]?.id;
  document.getElementById('folder-title').textContent = folderNames[activeFolder];
  document.getElementById('list-summary').textContent =
    `${visible.length} messages · ${visible.filter((message) => message.unread).length} unread`;
  document.getElementById('inbox-count').textContent = messages.filter((message) => message.folder === 'inbox').length;
  list.replaceChildren();
  for (const message of visible) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `message-row${message.id === selectedId ? ' selected' : ''}${message.unread ? ' unread' : ''}`;
    button.setAttribute('aria-pressed', String(message.id === selectedId));
    button.innerHTML = `<div class="row-top"><span class="row-sender">${message.unread ? '<span class="unread-dot"></span>' : ''}${message.sender}</span><time class="row-time">${message.time}</time></div><div class="row-subject">${message.subject}</div><div class="row-snippet">${message.snippet}</div><div class="row-meta">${message.account}${message.starred ? ' · Starred' : ''}${message.attachment ? ' · Attachment' : ''}</div>`;
    button.addEventListener('click', () => {
      selectedId = message.id;
      message.unread = false;
      app.dataset.reading = 'true';
      renderMessages();
    });
    list.append(button);
  }
  if (!visible.length)
    list.innerHTML = `<div class="empty-state"><strong>${search.value ? 'No matching messages' : 'No messages in this folder'}</strong>${search.value ? 'Try a different search.' : 'Choose another folder to view its messages.'}</div>`;
  renderDetail(visible);
  if (!focusWasInList) return;
  const backButton = document.getElementById('back-button');
  if (readingPaneLayout.matches && app.dataset.reading === 'true' && backButton.offsetParent) {
    backButton.focus();
    return;
  }
  focusMessageRow();
}
function setTheme(theme) {
  app.dataset.theme = theme;
  themeToggle.textContent = theme === 'dark' ? 'Light theme' : 'Dark theme';
}
function openComposer(mode = 'new') {
  const message = messages.find((item) => item.id === selectedId);
  document.getElementById('composer-title').textContent =
    mode === 'new' ? 'New message' : mode === 'reply' ? 'Reply' : 'Forward';
  document.getElementById('compose-to').value = mode === 'reply' && message ? message.address : '';
  document.getElementById('compose-subject').value =
    mode === 'new' || !message ? '' : `${mode === 'reply' ? 'Re:' : 'Fwd:'} ${message.subject}`;
  composer.querySelector('textarea').value = '';
  composer.showModal();
}
for (const button of document.querySelectorAll('[data-folder]')) {
  button.addEventListener('click', () => {
    activeFolder = button.dataset.folder;
    document.getElementById('mobile-folders').value = activeFolder;
    app.dataset.reading = 'false';
    for (const folder of document.querySelectorAll('[data-folder]')) {
      folder.classList.toggle('active', folder === button);
      folder.setAttribute('aria-pressed', String(folder === button));
    }
    renderMessages();
  });
}
themeToggle.addEventListener('click', () => setTheme(app.dataset.theme === 'dark' ? 'light' : 'dark'));
densityToggle.addEventListener('click', () => {
  const compact = app.dataset.density !== 'compact';
  app.dataset.density = compact ? 'compact' : 'comfortable';
  densityToggle.textContent = compact ? 'Comfortable view' : 'Compact view';
});
document.getElementById('mobile-folders').addEventListener('change', (event) => {
  document.querySelector(`[data-folder="${event.target.value}"]`).click();
});
search.addEventListener('input', renderMessages);
document.getElementById('archive-button').addEventListener('click', () => {
  const message = messages.find((item) => item.id === selectedId);
  if (message) {
    message.folder = 'archive';
    renderMessages();
    announce('Moved to Archive in this preview');
  }
});
document.getElementById('star-button').addEventListener('click', () => {
  const message = messages.find((item) => item.id === selectedId);
  if (message) {
    message.starred = !message.starred;
    renderMessages();
  }
});
document.getElementById('compose-button').addEventListener('click', () => openComposer());
document.getElementById('reply-button').addEventListener('click', () => openComposer('reply'));
document.getElementById('forward-button').addEventListener('click', () => openComposer('forward'));
document.getElementById('back-button').addEventListener('click', () => {
  app.dataset.reading = 'false';
  focusMessageRow();
});
document.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault();
    search.focus();
  }
});
setTheme(new URLSearchParams(location.search).get('theme') === 'dark' ? 'dark' : 'light');
renderMessages();
