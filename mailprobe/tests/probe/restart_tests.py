import unittest
from unittest.mock import Mock, patch

from mailprobe.tests.probe.scenario_restart import run


class RestartTests(unittest.TestCase):
    def fixture(self, with_delivery):
        client = Mock()
        baseline = {'id': 1, 'headerMessageId': 'draft', 'folder': {'id': 'drafts'}}
        client.read_record.return_value = dict.fromkeys(['plain', 'html', 'native_target'], baseline)
        client.evidence.return_value = (
            {'delivery': {'queued_message': baseline, 'queued_subject': 'Queued'}} if with_delivery else {}
        )
        client.call.side_effect = lambda action, _arguments: (
            {'messages': [baseline]} if action == 'query' else {'subject': 'Draft'}
        )
        client.command.return_value = {'ok': True, 'result': {'messages': [baseline]}}
        client.messages.return_value = []
        return client

    def test_unattended_restart_rediscovers_drafts_without_delivery_record(self):
        client = self.fixture(with_delivery=False)
        run(client)
        self.assertEqual(client.record.call_args.args[1]['queued']['status'], 'not_run')
        self.assertEqual(len(client.record.call_args.args[1]['drafts']), 3)
        for recovered in client.record.call_args.args[1]['drafts'].values():
            self.assertFalse(recovered['folder_selection_required'])
        self.assertTrue(all(command.args[0] == 'query' for command in client.command.call_args_list))
        client.messages.assert_not_called()

    def test_full_restart_also_verifies_queued_message(self):
        client = self.fixture(with_delivery=True)
        run(client)
        self.assertEqual(len(client.record.call_args.args[1]['queued']), 1)
        client.messages.assert_called_once_with('Queued')

    def test_restart_polls_read_only_identity_query_until_draft_is_visible(self):
        client = self.fixture(with_delivery=False)
        restored = {'id': 42, 'headerMessageId': 'draft', 'folder': {'id': 'drafts'}}
        client.command.side_effect = [
            {'ok': True, 'result': {'messages': []}},
            {'ok': True, 'result': {'folder_id': 'drafts'}},
            {'ok': True, 'result': {'messages': []}},
            *[{'ok': True, 'result': {'messages': [restored]}}] * 3,
        ]
        with patch('mailprobe.tests.probe.scenario_restart.time.sleep'):
            run(client)
        self.assertEqual(client.command.call_count, 6)
        selections = []
        for command in client.command.call_args_list:
            action, arguments = command.args
            if action == 'select_folder':
                selections.append(arguments)
                continue
            self.assertEqual(action, 'query')
            self.assertEqual(arguments, {'query': {'headerMessageId': 'draft', 'folderId': 'drafts'}})
            self.assertLessEqual(command.kwargs['timeout'], 10)
            self.assertLessEqual(command.kwargs['request_timeout'], 30)
        self.assertEqual(selections, [{'folder_id': 'drafts'}])
        for command in client.call.call_args_list:
            self.assertEqual(command.args, ('get_message', {'message_id': 42}))
        self.assertEqual(client.record.call_args.args[1]['drafts']['plain']['after']['id'], 42)
        self.assertEqual(client.record.call_args.args[1]['drafts']['plain']['initial_matches'], [])
        self.assertTrue(client.record.call_args.args[1]['drafts']['plain']['folder_selection_required'])

    def test_restart_stops_polling_after_deadline_without_mutation(self):
        client = self.fixture(with_delivery=False)
        client.command.return_value = {'ok': True, 'result': {'messages': []}}
        clock = Mock()
        clock.elapsed = 0

        def sleep(duration):
            clock.elapsed += duration

        with (
            patch(
                'mailprobe.tests.probe.scenario_restart.time.monotonic',
                side_effect=lambda: clock.elapsed,
            ),
            patch('mailprobe.tests.probe.scenario_restart.time.sleep', side_effect=sleep),
        ):
            with self.assertRaisesRegex(AssertionError, 'did not become queryable'):
                run(client)
        self.assertEqual(clock.elapsed, 30)
        self.assertEqual(
            sum(command.args[0] == 'select_folder' for command in client.command.call_args_list),
            1,
        )
        client.call.assert_not_called()
        client.record.assert_not_called()


if __name__ == '__main__':
    unittest.main()
