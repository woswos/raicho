import json
import uuid

from mailprobe.tests.profile.nss_credentials import encrypt, encryption_library


def write_credentials(profile):
    with encryption_library(profile) as library:
        login = {
            'id': 1,
            'hostname': 'imap://mail-proxy',
            'httpRealm': 'imap://mail-proxy',
            'formSubmitURL': None,
            'usernameField': '',
            'passwordField': '',
            'encryptedUsername': encrypt(library, 'sender'),
            'encryptedPassword': encrypt(library, 'fixture'),
            'guid': '{' + str(uuid.uuid4()) + '}',
            'encType': 1,
            'timeCreated': 0,
            'timeLastUsed': 0,
            'timePasswordChanged': 0,
            'timesUsed': 0,
        }
    destination = profile / 'logins.json'
    destination.write_text(
        json.dumps({'nextId': 2, 'logins': [login], 'version': 3}) + '\n'
    )
    destination.chmod(0o600)
