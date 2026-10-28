import argparse
import io
import os
import sys
import unittest

from automation import output


def summary(start, ran, skipped):
    location = '' if start == '.' else f' in {start}'
    skipped_text = f', {skipped} skipped' if skipped else ''
    return f'Python: {ran - skipped} tests passed{skipped_text}{location}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start')
    parser.add_argument('pattern')
    arguments = parser.parse_args()
    verbose = output.verbose()
    # Tests must not inherit the caller's output mode.
    os.environ.pop('VERBOSE', None)
    suite = unittest.defaultTestLoader.discover(arguments.start, pattern=arguments.pattern, top_level_dir='.')
    report = sys.stdout if verbose else io.StringIO()
    result = unittest.TextTestRunner(stream=report, buffer=not verbose, verbosity=2 if verbose else 1).run(suite)
    if not result.wasSuccessful():
        if not verbose:
            sys.stdout.write(report.getvalue())
        return 1
    if result.testsRun == 0:
        print(f'FAIL: no tests matched {arguments.pattern} in {arguments.start}', file=sys.stderr)
        return 1
    print(summary(arguments.start, result.testsRun, len(result.skipped)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
