import argparse
import io
import multiprocessing
import os
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor

from automation import output


def summary(start, ran, skipped):
    location = '' if start == '.' else f' in {start}'
    skipped_text = f', {skipped} skipped' if skipped else ''
    return f'Python: {ran - skipped} tests passed{skipped_text}{location}'


# Forked workers inherit these discovered module suites, so each runs its tests exactly as discovery found them.
SUITES = []


def run_suite(index, verbose):
    report = io.StringIO()
    runner = unittest.TextTestRunner(stream=report, buffer=not verbose, verbosity=2 if verbose else 1)
    result = runner.run(SUITES[index])
    return result.testsRun, len(result.skipped), result.wasSuccessful(), report.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start')
    parser.add_argument('pattern')
    arguments = parser.parse_args()
    verbose = output.verbose()
    # Tests must not inherit the caller's output mode.
    os.environ.pop('VERBOSE', None)
    SUITES[:] = unittest.defaultTestLoader.discover(arguments.start, pattern=arguments.pattern, top_level_dir='.')
    ran = skipped = 0
    successful = True
    # Modules run in separate processes, so their tests share no interpreter state.
    # A fork pool starts every worker at once, so it starts no more than there are modules.
    workers = max(1, min(len(SUITES), os.process_cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context('fork')) as pool:
        for count, skips, passed, report in pool.map(run_suite, range(len(SUITES)), [verbose] * len(SUITES)):
            ran += count
            skipped += skips
            successful = successful and passed
            if verbose or not passed:
                sys.stdout.write(report)
    if not successful:
        return 1
    if ran == 0:
        print(f'FAIL: no tests matched {arguments.pattern} in {arguments.start}', file=sys.stderr)
        return 1
    print(summary(arguments.start, ran, skipped))
    return 0


if __name__ == '__main__':
    sys.exit(main())
