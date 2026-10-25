import argparse
import json
from pathlib import Path

from profile_credentials import write_credentials
from profile_settings import preferences

MARKER = 'raicho_mail_fixture'
MARKER_CONTENT = 'raicho-mail-fixture-v1\n'


def seed_profile(profile):
    if profile.is_symlink():
        raise ValueError('The disposable profile cannot be a symlink.')
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = profile / MARKER
    if marker.exists():
        if marker.is_symlink() or marker.read_text() != MARKER_CONTENT:
            raise ValueError('The disposable profile marker is not recognized.')
        if not all((profile / name).is_file() for name in ['user.js', 'logins.json']):
            raise ValueError('The disposable profile is incomplete.')
        return False
    if any(profile.iterdir()):
        raise ValueError('Seeding requires an empty disposable profile.')
    profile.chmod(0o700)
    configured = preferences()
    destination = profile / 'user.js'
    destination.write_text(
        ''.join(
            f'user_pref({json.dumps(name)}, {json.dumps(value)});\n'
            for name, value in sorted(configured.items())
        )
    )
    destination.chmod(0o600)
    write_credentials(profile)
    marker.write_text(MARKER_CONTENT)
    marker.chmod(0o600)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, default=Path('/config/profile'))
    arguments = parser.parse_args()
    seeded = seed_profile(arguments.profile)
    print('Disposable profile seeded.' if seeded else 'Disposable profile preserved.')


if __name__ == '__main__':
    main()
