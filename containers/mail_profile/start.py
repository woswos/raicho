import os
import sys
from pathlib import Path

from seed_profile import seed_profile


def main():
    seed_profile(Path('/config/profile'))
    os.execv(sys.executable, [sys.executable, '-B', '/opt/raicho/runtime.py'])


if __name__ == '__main__':
    main()
