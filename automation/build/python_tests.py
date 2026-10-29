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


def modules(suite, names, broken):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            modules(test, names, broken)
        elif isinstance(test, unittest.loader._FailedTest):
            broken.addTest(test)
        elif type(test).__module__ not in names:
            names.append(type(test).__module__)
    return names


def run_module(name, verbose):
    report = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName(name)
    result = unittest.TextTestRunner(stream=report, buffer=not verbose, verbosity=2 if verbose else 1).run(suite)
    return result.testsRun, len(result.skipped), result.wasSuccessful(), report.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start')
    parser.add_argument('pattern')
    arguments = parser.parse_args()
    verbose = output.verbose()
    # Tests must not inherit the caller's output mode.
    os.environ.pop('VERBOSE', None)
    suite = unittest.defaultTestLoader.discover(arguments.start, pattern=arguments.pattern, top_level_dir='.')
    broken = unittest.TestSuite()
    names = modules(suite, [], broken)
    ran = skipped = 0
    successful = True
    if broken.countTestCases():
        successful = unittest.TextTestRunner(stream=sys.stdout).run(broken).wasSuccessful()
    # Modules run in separate processes, so their tests share no interpreter state.
    # A fork pool starts every worker at once, so it starts no more than there are modules.
    workers = max(1, min(len(names), os.process_cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context('fork')) as pool:
        for count, skips, passed, report in pool.map(run_module, names, [verbose] * len(names)):
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
