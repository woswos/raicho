import argparse
import io
import os
import sys
import unittest


def summary(start, ran, skipped):
    location = '' if start == '.' else f' in {start}'
    skipped_text = f', {skipped} skipped' if skipped else ''
    return f'Python: {ran - skipped} tests passed{skipped_text}{location}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start')
    parser.add_argument('pattern')
    arguments = parser.parse_args()
    # Tests must not inherit the caller's output mode.
    verbose = bool(os.environ.pop('VERBOSE', None))
    suite = unittest.defaultTestLoader.discover(arguments.start, pattern=arguments.pattern, top_level_dir='.')
    if verbose:
        return 0 if unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite).wasSuccessful() else 1
    report = io.StringIO()
    result = unittest.TextTestRunner(stream=report, buffer=True).run(suite)
    if not result.wasSuccessful():
        sys.stdout.write(report.getvalue())
        return 1
    if result.testsRun == 0:
        print(f'FAIL: no tests matched {arguments.pattern} in {arguments.start}', file=sys.stderr)
        return 1
    print(summary(arguments.start, result.testsRun, len(result.skipped)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
