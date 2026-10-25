import unittest
from unittest.mock import Mock

from mailprobe.tests.probe.scenario_permissions import record_skips, verify


class PermissionTests(unittest.TestCase):
    def test_verified_permission_is_recorded(self):
        client = Mock()
        client.call.return_value = {'send_allowed': True}
        verify(client)
        client.call.assert_called_once_with('permission_status')
        self.assertEqual(client.record.call_args.args[0], 'send_permission')
        self.assertEqual(client.record.call_args.args[1]['status'], 'granted')

    def test_missing_permission_never_records_success(self):
        for allowed in [False, None, 'true']:
            client = Mock()
            client.call.return_value = {'send_allowed': allowed}
            with self.assertRaisesRegex(AssertionError, 'Grant messages.send'):
                verify(client)
            client.record.assert_not_called()

    def test_unattended_run_records_all_interactive_cases_as_not_run(self):
        client = Mock()
        record_skips(client)
        self.assertEqual(
            [record.args[0] for record in client.record.call_args_list],
            ['delivery', 'native', 'faults'],
        )
        for record in client.record.call_args_list:
            self.assertEqual(record.args[1]['status'], 'not_run')


if __name__ == '__main__':
    unittest.main()
