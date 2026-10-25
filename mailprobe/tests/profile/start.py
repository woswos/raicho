import os
import sys
from pathlib import Path

from mailprobe.tests.profile.seed import seed_profile


def main():
    seed_profile(Path('/config/profile'))
    os.execv(sys.executable, [sys.executable, '-B', '-m', 'thunderbird.runtime'])


if __name__ == '__main__':
    main()
