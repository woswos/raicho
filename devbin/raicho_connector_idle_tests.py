import unittest
from unittest.mock import Mock

from raicho_connector_idle import observe_idle


class ConnectorIdleTests(unittest.TestCase):
    def setUp(self):
        self.elapsed = 0
        self.sample = {
            'status': 'connected',
            'generation': 'a' * 32,
            'heartbeat_count': 1,
        }

    def pause(self, seconds):
        self.elapsed += seconds

    def observe(self, sample):
        return observe_idle(
            seconds=600,
            sample=sample,
            clock=lambda: self.elapsed,
            pause=self.pause,
            report=Mock(),
        )

    def test_observes_full_ten_minutes_with_progress_in_one_generation(self):
        def sample():
            return self.sample | {'heartbeat_count': 1 + self.elapsed // 15}

        self.observe(sample)
        self.assertEqual(self.elapsed, 600)

    def test_reconnection_cannot_pass_as_persistent_background_activity(self):
        def sample():
            return self.sample | {'generation': ('b' if self.elapsed else 'a') * 32}

        with self.assertRaisesRegex(AssertionError, 'session changed'):
            self.observe(sample)
        self.assertLess(self.elapsed, 600)

    def test_connected_status_without_heartbeat_progress_fails_early(self):
        with self.assertRaisesRegex(AssertionError, 'heartbeat stopped'):
            self.observe(lambda: self.sample)
        self.assertLessEqual(self.elapsed, 60)

    def test_disconnection_and_counter_reset_fail_without_echoing_payload(self):
        for change in (
            {'status': 'disconnected'},
            {'heartbeat_count': 0},
            {'heartbeat_count': True},
        ):
            self.elapsed = 0

            def sample(change=change):
                return self.sample | (change if self.elapsed else {})

            with self.assertRaises(AssertionError):
                self.observe(sample)

    def test_observation_errors_are_not_ignored(self):
        with self.assertRaises(OSError):
            self.observe(Mock(side_effect=OSError('unreachable')))
