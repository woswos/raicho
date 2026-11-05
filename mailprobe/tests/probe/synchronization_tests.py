import unittest
from unittest.mock import Mock, patch

from mailprobe.tests.probe import scenario_synchronization

IMAP_ACCOUNT = {
    'type': 'imap',
    'rootFolder': {'path': '/', 'id': 'imap:/'},
    'folders': [
        {'path': '/INBOX', 'id': 'imap:/INBOX', 'subFolders': []},
        {
            'path': '/Work',
            'id': 'imap:/Work',
            'subFolders': [{'path': '/Projects', 'id': 'imap:/Projects'}],
        },
    ],
}
INVENTORY = {'accounts': [{'type': 'none', 'folders': [{'path': '/Trash', 'id': 'local:/Trash'}]}, IMAP_ACCOUNT]}
BEFORE_CREATION = {'accounts': [IMAP_ACCOUNT | {'folders': IMAP_ACCOUNT['folders'][:1]}]}


class SynchronizationTests(unittest.TestCase):
    def test_folders_come_from_the_imap_account_tree(self):
        self.assertEqual(
            scenario_synchronization.account_folders(INVENTORY),
            {'INBOX': 'imap:/INBOX', 'Projects': 'imap:/Projects'},
        )

    def test_unlisted_folders_wait_for_thunderbird(self):
        self.assertIsNone(scenario_synchronization.account_folders(BEFORE_CREATION))

    def test_prepare_creates_the_folder_through_thunderbird_and_records_unknown_server_folders(self):
        client = Mock()
        responses = {'inventory': [BEFORE_CREATION, INVENTORY], 'query': [{'messages': []}, {'messages': []}]}
        client.call.side_effect = lambda action, _arguments=None: (
            responses[action].pop(0) if action in responses else {}
        )
        scenario_synchronization.prepare(client)
        client.call.assert_any_call('create_folder', {'parent_id': 'imap:/', 'name': 'Projects'})
        evidence = client.record.call_args.args[1]
        self.assertEqual(evidence['server_folders_unknown_to_thunderbird'], ['Drafts', 'Sent', 'Trash'])

    def test_prepare_requires_absent_fixture_messages(self):
        client = Mock()
        client.call.side_effect = [BEFORE_CREATION, {}, INVENTORY, {'messages': []}, {'messages': [{'id': 1}]}]
        with self.assertRaises(AssertionError):
            scenario_synchronization.prepare(client)
        client.record.assert_not_called()

    def test_seed_appends_one_message_per_folder_without_a_connection(self):
        client = Mock()
        with patch('mailprobe.tests.probe.scenario_synchronization.append_message') as append:
            scenario_synchronization.seed(client)
        self.assertEqual([call.args[1] for call in append.call_args_list], ['INBOX', 'Projects'])
        self.assertEqual(append.call_args.args[2]['Subject'], 'Raicho synchronization fixture Projects')
        client.wait_connected.assert_not_called()

    def test_run_polls_queries_and_never_selects_a_folder(self):
        client = Mock()
        client.call.return_value = INVENTORY
        client.command.side_effect = [
            {'ok': True, 'result': {'messages': messages}} for messages in ([], [{'id': 1}], [{'id': 2}])
        ]
        with patch('mailprobe.tests.probe.scenario_synchronization.time.sleep'):
            scenario_synchronization.run(client)
        self.assertEqual({call.args[0] for call in client.command.call_args_list}, {'query'})
        evidence = client.record.call_args.args[1]
        self.assertEqual(evidence['results']['INBOX']['attempts'], 2)
        self.assertEqual(evidence['results']['Projects']['attempts'], 1)

    def test_run_records_and_fails_when_discovery_misses_the_deadline(self):
        client = Mock()
        client.call.return_value = INVENTORY
        client.command.return_value = {'ok': True, 'result': {'messages': []}}
        clock = Mock()
        clock.elapsed = 0

        def sleep(duration):
            clock.elapsed += duration

        with (
            patch(
                'mailprobe.tests.probe.scenario_synchronization.time.monotonic',
                side_effect=lambda: clock.elapsed,
            ),
            patch('mailprobe.tests.probe.scenario_synchronization.time.sleep', side_effect=sleep),
        ):
            with self.assertRaisesRegex(AssertionError, 'INBOX'):
                scenario_synchronization.run(client)
        self.assertFalse(client.record.call_args.args[1]['results']['Projects']['found'])

    def test_run_rejects_a_match_that_arrives_after_the_deadline(self):
        client = Mock()
        client.call.return_value = INVENTORY
        clock = Mock()
        clock.elapsed = 0

        def late_query(_action, _arguments, **_options):
            clock.elapsed += scenario_synchronization.DEADLINE_SECONDS + 1
            return {'ok': True, 'result': {'messages': [{'id': 1}]}}

        client.command.side_effect = late_query
        with patch('mailprobe.tests.probe.scenario_synchronization.time.monotonic', side_effect=lambda: clock.elapsed):
            with self.assertRaisesRegex(AssertionError, 'INBOX'):
                scenario_synchronization.run(client)
        results = client.record.call_args.args[1]['results']
        self.assertEqual([result['found'] for result in results.values()], [False, False])

    def test_run_skips_queries_once_the_deadline_has_passed(self):
        client = Mock()
        client.call.return_value = INVENTORY
        clock = Mock()
        clock.elapsed = 0

        def slow_query(_action, _arguments, **_options):
            clock.elapsed += scenario_synchronization.DEADLINE_SECONDS + 1
            return {'ok': True, 'result': {'messages': []}}

        client.command.side_effect = slow_query
        with patch('mailprobe.tests.probe.scenario_synchronization.time.monotonic', side_effect=lambda: clock.elapsed):
            with self.assertRaisesRegex(AssertionError, 'INBOX'):
                scenario_synchronization.run(client)
        self.assertEqual(client.command.call_count, 1)
        results = client.record.call_args.args[1]['results']
        self.assertEqual(results['Projects']['attempts'], 0)
        self.assertFalse(results['Projects']['found'])

    def test_run_counts_the_deadline_from_the_restart(self):
        client = Mock()
        client.call.return_value = INVENTORY
        client.command.return_value = {'ok': True, 'result': {'messages': [{'id': 1}]}}
        with (
            patch('mailprobe.tests.probe.scenario_synchronization.time.time', return_value=1000.0),
            patch('mailprobe.tests.probe.scenario_synchronization.time.monotonic', return_value=0.0),
        ):
            with self.assertRaisesRegex(AssertionError, 'INBOX'):
                scenario_synchronization.run(client, restarted_at=800.0)
        evidence = client.record.call_args.args[1]
        self.assertEqual(evidence['seconds_before_polling'], 200)
        self.assertFalse(evidence['results']['INBOX']['found'])


if __name__ == '__main__':
    unittest.main()
