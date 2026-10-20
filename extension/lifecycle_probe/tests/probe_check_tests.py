import unittest

from probe_check import check_observations


class ProbeCheckTests(unittest.TestCase):
    def setUp(self):
        self.session = {
            'session_id': 'session-one',
            'extension_version': '0.1.0',
            'browser_version': '153.5.0',
            'origin': None,
            'first_seen': 10,
            'last_seen': 80,
            'heartbeat_count': 7,
            'sequence': 7,
        }
        self.observations = {'sessions': [self.session], 'rejections': 0}

    def check(self, **options):
        return check_observations(self.observations, '0.1.0', 2, 60, now=85, **options)

    def test_live_session_passes_with_idle_evidence(self):
        self.assertEqual(self.check()['session_id'], 'session-one')

    def test_baseline_requires_a_new_session(self):
        with self.assertRaises(ValueError):
            self.check(baseline=self.observations)
        baseline = {'sessions': [self.session | {'session_id': 'previous'}]}
        self.assertEqual(self.check(baseline=baseline)['session_id'], 'session-one')

    def test_idle_checkpoint_requires_the_same_session(self):
        self.assertEqual(
            self.check(baseline=self.observations, same_session=True)['session_id'],
            'session-one',
        )
        baseline = {'sessions': [self.session | {'session_id': 'previous'}]}
        with self.assertRaises(ValueError):
            self.check(baseline=baseline, same_session=True)

    def test_insufficient_or_stale_evidence_fails(self):
        for changes in [
            {'extension_version': '0.2.0'},
            {'heartbeat_count': 1},
            {'last_seen': 20},
            {'first_seen': 50},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                check_observations(
                    {'sessions': [self.session | changes], 'rejections': 0},
                    '0.1.0',
                    2,
                    60,
                    now=85,
                )

    def test_rejected_input_fails_acceptance(self):
        with self.assertRaises(ValueError):
            check_observations(
                self.observations | {'rejections': 1}, '0.1.0', 2, 60, now=85
            )


if __name__ == '__main__':
    unittest.main()
