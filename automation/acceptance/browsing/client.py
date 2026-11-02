import json
import urllib.error
import urllib.request

RAICHO_URL = 'http://raicho:8080'
# The deployment's default RAICHO_PUBLIC_ORIGIN, which every mutation must name.
ORIGIN = 'http://localhost:8080'
COOKIE = 'raicho_session'


class Browser:
    """A browser stand-in that keeps one session cookie and sends the page's headers."""

    def __init__(self, base=RAICHO_URL, cookie=None):
        self.base = base
        self.cookie = cookie

    def request(self, method, path, body=None):
        headers = {'Accept': 'application/json'}
        if method not in ('GET', 'HEAD'):
            headers |= {'Origin': ORIGIN, 'Sec-Fetch-Site': 'same-origin', 'Content-Type': 'application/json'}
        if self.cookie:
            headers['Cookie'] = f'{COOKIE}={self.cookie}'
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(f'{self.base}{path}', data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, read(response), response.headers
        except urllib.error.HTTPError as error:
            return error.code, read(error), error.headers

    def get(self, path):
        return self.request('GET', path)

    def sign_in(self, password):
        status, document, headers = self.request('POST', '/api/session', {'password': password})
        assert status == 200, f'Login failed with {status}: {document}'
        self.cookie = session_cookie(headers.get_all('Set-Cookie') or [])
        return self.cookie


def read(response):
    body = response.read()
    return json.loads(body) if body else None


def session_cookie(values):
    for value in values:
        name, _, rest = value.partition('=')
        if name == COOKIE:
            token = rest.split(';', 1)[0]
            assert len(token) == 64, 'The session cookie has an unexpected format'
            assert 'HttpOnly' in value and 'SameSite=Strict' in value, 'The session cookie is not protected'
            return token
    raise AssertionError('Login set no session cookie')
