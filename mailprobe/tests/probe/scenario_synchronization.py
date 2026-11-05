import time
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

from mailprobe.tests.probe.client import wait_until
from mailprobe.tests.proxy.mail_inspect import append_message

FOLDERS = ('INBOX', 'Projects')
SERVER_FOLDERS = ('Drafts', 'Sent', 'Trash')
DEADLINE_SECONDS = 150


def subject(folder):
    return f'Raicho synchronization fixture {folder}'


def imap_account(inventory):
    return next(account for account in inventory['accounts'] if account['type'] == 'imap')


def known_folders(account):
    pending = list(account['folders'])
    folders = {}
    while pending:
        folder = pending.pop()
        folders[folder['path'].removeprefix('/')] = folder['id']
        pending.extend(folder.get('subFolders', []))
    return folders


def account_folders(inventory):
    folders = known_folders(imap_account(inventory))
    if not all(name in folders for name in FOLDERS):
        return None
    return {name: folders[name] for name in FOLDERS}


def listed_folders(client, timeout=DEADLINE_SECONDS):
    started = time.monotonic()
    folders = wait_until(
        lambda: account_folders(client.call('inventory')),
        timeout,
        f'Thunderbird did not list the fixture folders: {list(FOLDERS)}',
    )
    return folders, round(time.monotonic() - started)


def prepare(client):
    account = imap_account(client.call('inventory'))
    # A folder that exists only on the server stays unknown until the folder pane expands its account.
    server_only = sorted(set(SERVER_FOLDERS) - set(known_folders(account)))
    client.call('create_folder', {'parent_id': account['rootFolder']['id'], 'name': 'Projects'})
    folders, seconds = listed_folders(client)
    for folder, identifier in folders.items():
        matches = client.call('query', {'query': {'subject': subject(folder), 'folderId': identifier}})
        assert not matches['messages'], matches
    client.record(
        'synchronization_folders',
        {'folders': folders, 'listing_seconds': seconds, 'server_folders_unknown_to_thunderbird': server_only},
    )


def seed(client):
    for folder in FOLDERS:
        message = EmailMessage()
        message['From'] = 'recipient@raicho.test'
        message['To'] = 'sender@raicho.test'
        message['Subject'] = subject(folder)
        message['Date'] = format_datetime(datetime.now(UTC))
        message['Message-ID'] = make_msgid(domain='raicho.test')
        message.set_content('Delivered while Thunderbird was stopped.')
        append_message('sender', folder, message)
    client.record('synchronization_seed', {'folders': list(FOLDERS), 'thunderbird': 'stopped'})


def discover(client, folder, identifier, deadline):
    attempts = 0
    started = deadline - DEADLINE_SECONDS
    while True:
        attempts += 1
        remaining = deadline - time.monotonic()
        response = client.command(
            'query',
            {'query': {'subject': subject(folder), 'folderId': identifier}},
            timeout=max(1, min(10, remaining)),
            request_timeout=max(1, remaining) + 10,
        )
        assert response['ok'], response
        if response['result']['messages'] and time.monotonic() < deadline:
            return {'found': True, 'attempts': attempts, 'seconds': round(time.monotonic() - started)}
        if time.monotonic() >= deadline:
            return {'found': False, 'attempts': attempts, 'seconds': round(time.monotonic() - started)}
        time.sleep(1)


def run(client, restarted_at=None):
    client.wait_connected()
    deadline = time.monotonic() + DEADLINE_SECONDS
    if restarted_at is not None:
        deadline -= time.time() - restarted_at
    folders, listing_seconds = listed_folders(client, deadline - time.monotonic())
    seconds_before_polling = round(time.monotonic() - (deadline - DEADLINE_SECONDS))
    results = {folder: discover(client, folder, identifier, deadline) for folder, identifier in folders.items()}
    client.record(
        'synchronization',
        {
            'deadline_seconds': DEADLINE_SECONDS,
            'seconds_before_polling': seconds_before_polling,
            'listing_seconds': listing_seconds,
            'folder_selection': 'never',
            'results': results,
        },
    )
    missing = [folder for folder, result in results.items() if not result['found']]
    assert not missing, f'Messages delivered while Thunderbird was stopped were not discovered: {missing}'
