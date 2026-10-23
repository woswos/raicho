import io
import json
import unittest
from unittest.mock import Mock

from runtime.credentials.raicho_wait_connector import wait_for_connector


class ConnectorReadinessTests(unittest.TestCase):
    @staticmethod
    def response(status, heartbeats=0, application='ready'):
        return io.BytesIO(
            json.dumps(
                {
                    'status': application,
                    'backend': {
                        'kind': 'thunderbird',
                        'status': status,
                        'heartbeat_count': heartbeats,
                    },
                }
            ).encode()
        )

    def test_waits_for_authenticated_heartbeat_not_only_http_readiness(self):
        request = Mock(
            side_effect=[
                self.response('disconnected'),
                self.response('connected'),
                self.response('connected', 1),
            ]
        )
        pause = Mock()
        wait_for_connector(request=request, pause=pause, clock=lambda: 0)
        self.assertEqual(request.call_count, 3)
        self.assertEqual(pause.call_count, 2)

    def test_failures_are_bounded_and_do_not_echo_response_content(self):
        request = Mock(
            side_effect=[
                OSError('private endpoint details'),
                io.BytesIO(b'private malformed response'),
                self.response('connected', 1, application='unavailable'),
            ]
        )
        with self.assertRaisesRegex(
            ValueError,
            '^Thunderbird did not establish an authenticated connection in time$',
        ):
            wait_for_connector(
                timeout=4,
                request=request,
                pause=Mock(),
                clock=iter([0, 1, 2, 3, 4]).__next__,
            )
        self.assertEqual(request.call_count, 3)

    def test_rejects_revoked_or_unconfigured_backend_without_retry(self):
        for status in ('revoked', 'unconfigured'):
            request = Mock(return_value=self.response(status))
            with self.assertRaisesRegex(
                ValueError, '^Connector credential is not active$'
            ):
                wait_for_connector(request=request, pause=Mock(), clock=lambda: 0)
            self.assertEqual(request.call_count, 1)
