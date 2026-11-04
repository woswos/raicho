import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from automation.acceptance.browsing.client import ORIGIN, Browser, session_cookie

TOKEN = 'a' * 64


class Recorder(BaseHTTPRequestHandler):
    requests = []

    def respond(self):
        length = int(self.headers.get('Content-Length') or 0)
        Recorder.requests.append((self.command, self.path, dict(self.headers), self.rfile.read(length)))
        if self.path == '/api/session' and self.command == 'POST':
            body = json.dumps({'authenticated': True}).encode()
            self.send_response(200)
            self.send_header('Set-Cookie', f'raicho_session={TOKEN}; Path=/; HttpOnly; SameSite=Strict; Max-Age=60')
        else:
            body = json.dumps({'error': 'unauthenticated'}).encode()
            self.send_response(401)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = respond

    def log_message(self, *_arguments):
        pass


class BrowserClientTests(unittest.TestCase):
    def setUp(self):
        Recorder.requests = []
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Recorder)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.server.server_close)
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def test_login_sends_page_headers_and_later_requests_carry_the_cookie(self):
        browser = Browser(self.base)
        self.assertEqual(browser.sign_in('fictional password'), TOKEN)
        status, document, _ = browser.get('/api/mail/accounts')
        self.assertEqual((status, document), (401, {'error': 'unauthenticated'}))
        (_, _, login, body), (_, _, follow_up, _) = Recorder.requests
        self.assertEqual(login['Origin'], ORIGIN)
        self.assertEqual(login['Sec-Fetch-Site'], 'same-origin')
        self.assertEqual(json.loads(body), {'password': 'fictional password'})
        self.assertNotIn('Origin', follow_up)
        self.assertEqual(follow_up['Cookie'], f'raicho_session={TOKEN}')

    def test_unprotected_or_missing_cookies_fail(self):
        for values in (
            [],
            ['other=1'],
            [f'raicho_session={TOKEN}; Path=/'],
            ['raicho_session=short; HttpOnly; SameSite=Strict'],
        ):
            with self.subTest(values=values), self.assertRaises(AssertionError):
                session_cookie(values)


if __name__ == '__main__':
    unittest.main()
