import argparse
import json
import sys
import time
import urllib.error
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path
from urllib.parse import quote

from automation.acceptance.browsing.client import Browser
from mailprobe.tests.proxy.mail_inspect import append_message

STATE = Path('/state')
MESSAGES = 120
CANARY = 'raicho-browsing-canary'
DEADLINE_SECONDS = 150


def wait_until(attempt, failure, timeout=DEADLINE_SECONDS):
    deadline = time.monotonic() + timeout
    while (result := attempt()) is None:
        if time.monotonic() > deadline:
            raise AssertionError(failure)
        time.sleep(1)
    return result


def save(**values):
    path = STATE / 'state.json'
    state = json.loads(path.read_text()) if path.exists() else {}
    path.write_text(json.dumps(state | values))


def load():
    return json.loads((STATE / 'state.json').read_text())


def password():
    return (STATE / 'password').read_text().strip()


def connection():
    """Waits for a heartbeating connector and returns its generation."""

    def connected():
        try:
            status = Browser().get('/api/status')[1]
        except (urllib.error.URLError, ConnectionError):
            return None
        backend = status['backend']
        return backend['generation'] if backend['status'] == 'connected' and backend['heartbeat_count'] else None

    return wait_until(connected, 'Thunderbird did not connect')


def seed():
    started = datetime(2026, 11, 3, 8, 0, tzinfo=UTC)

    def appended(index):
        message = EmailMessage()
        message['From'] = f'Zoë {index} <recipient@raicho.test>'
        message['To'] = 'sender@raicho.test'
        message['Subject'] = f'{CANARY} {index:03d} Grüße'
        message['Date'] = format_datetime(started + timedelta(minutes=index))
        message['Message-ID'] = make_msgid(domain='raicho.test')
        message.set_content(f'{CANARY} body {index}')
        try:
            append_message('sender', 'INBOX', message)
        except OSError:
            return None
        return True

    wait_until(lambda: appended(0), 'GreenMail did not accept fixture mail')
    for index in range(1, MESSAGES):
        assert appended(index), 'GreenMail rejected fixture mail'
    print(f'Seeded {MESSAGES} fictional messages')


def inbox(browser):
    status, document, _ = browser.get('/api/mail/accounts')
    assert status == 200, document
    account = next(account for account in document['accounts'] if account['name'] == 'Disposable mail fixture')
    assert [identity['email'] for identity in account['identities']] == ['sender@raicho.test', 'alias@raicho.test']
    status, document, _ = browser.get(f'/api/mail/accounts/{quote(account["id"])}/mailboxes')
    assert status == 200 and not document['truncated'], document
    return next(mailbox for mailbox in document['mailboxes'] if mailbox.get('role') == 'inbox')


def all_summaries(browser, mailbox):
    status, page, _ = browser.get(f'/api/mail/mailboxes/{quote(mailbox["id"])}/messages')
    assert status == 200, page
    pages = [page]
    while 'cursor' in pages[-1]:
        status, page, _ = browser.get(f'/api/mail/cursors/{pages[-1]["cursor"]}')
        assert status == 200, page
        pages.append(page)
    return pages


def browse():
    generation = connection()
    anonymous = Browser()
    status, document, _ = anonymous.get('/api/mail/accounts')
    assert (status, document) == (401, {'error': 'unauthenticated'}), document
    first, second = Browser(), Browser()
    first.sign_in(password())
    second.sign_in(password())
    mailbox = inbox(first)

    def complete():
        pages = all_summaries(first, mailbox)
        subjects = [summary['subject'] for page in pages for summary in page['messages']]
        return pages if len([subject for subject in subjects if subject.startswith(CANARY)]) == MESSAGES else None

    pages = wait_until(complete, 'Thunderbird did not list every fixture message')
    summaries = [summary for page in pages for summary in page['messages']]
    assert len(pages) >= 3 and len({summary['id'] for summary in summaries}) == len(summaries), 'Pages overlap'
    dates = [summary['date'] for summary in summaries]
    assert dates == sorted(dates, reverse=True), 'Summaries are not newest first'
    assert summaries[0]['subject'] == f'{CANARY} {MESSAGES - 1:03d} Grüße', summaries[0]
    status, page, _ = second.get(f'/api/mail/mailboxes/{quote(mailbox["id"])}/messages')
    assert status == 200 and 'cursor' in page, page
    status, document, _ = first.get(f'/api/mail/cursors/{page["cursor"]}')
    assert (status, document) == (409, {'error': 'stale_cursor'}), 'A cursor crossed sessions'
    assert first.request('PUT', '/api/preferences', {'theme': 'dark'})[0] == 200
    status, _, _ = first.request('DELETE', '/api/session')
    assert status == 204 and first.get('/api/session')[0] == 401, 'Logout did not end the session'
    assert second.get('/api/session')[0] == 200, 'Logout ended another session'
    save(session=second.cookie, mailbox=mailbox, cursor=page['cursor'], generation=generation)
    print(f'Browsed {len(summaries)} summaries in {len(pages)} pages with two sessions')


def stale():
    state = load()
    wait_until(lambda: connection() != state['generation'] or None, 'Thunderbird did not reconnect')
    browser = Browser(cookie=state['session'])
    status, document, _ = browser.get(f'/api/mail/mailboxes/{quote(state["mailbox"]["id"])}/messages')
    assert (status, document) == (409, {'error': 'stale_handle'}), document
    status, document, _ = browser.get(f'/api/mail/cursors/{state["cursor"]}')
    assert (status, document) == (409, {'error': 'stale_cursor'}), document
    mailbox = inbox(browser)
    assert mailbox['id'] != state['mailbox']['id'], 'A restarted Thunderbird reused a handle'
    summaries = [summary for page in all_summaries(browser, mailbox) for summary in page['messages']]
    assert len(summaries) >= MESSAGES, 'The reloaded mailbox is incomplete'
    print('Handles and cursors from before the Thunderbird restart were stale, and new ones worked')


def persisted():
    connection()
    browser = Browser(cookie=load()['session'])
    assert browser.get('/api/session')[0] == 200, 'The session did not survive a Raicho restart'
    status, document, _ = browser.get('/api/preferences')
    assert (status, document) == (200, {'theme': 'dark'}), document
    print('The session and theme preference survived a Raicho restart')


def revoked():
    status, document, _ = Browser(cookie=load()['session']).get('/api/session')
    assert (status, document) == (401, {'error': 'unauthenticated'}), document
    print('Revocation ended the remaining session')


def privacy():
    markers = (CANARY.encode(), 'Grüße'.encode(), b'recipient@raicho.test')
    sources = {'logs': sys.stdin.buffer.read()}
    for path in Path('/fixture/raicho').iterdir():
        if path.is_file():
            sources[path.name] = path.read_bytes()
    for name, contents in sources.items():
        assert not any(marker in contents for marker in markers), f'{name} retained mail data'
    print(f'No mail data in Raicho logs or {len(sources) - 1} database files')


PHASES = {
    'seed': seed,
    'browse': browse,
    'stale': stale,
    'persisted': persisted,
    'revoked': revoked,
    'privacy': privacy,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=sorted(PHASES))
    PHASES[parser.parse_args().phase]()


if __name__ == '__main__':
    main()
