import unittest
from unittest.mock import Mock, call, patch

from scenario_helpers import saved_message, wait_query


class ScenarioHelpersTests(unittest.TestCase):
    def test_empty_save_result_polls_without_repeating_save(self):
        client = Mock()
        client.call.return_value = {'mode': 'draft', 'messages': []}
        client.command.side_effect = [
            {'ok': True, 'result': {'messages': [{'id': 1}]}},
            {'ok': True, 'result': {'messages': [{'id': 1}]}},
            {'ok': True, 'result': {'messages': [{'id': 1}, {'id': 2}]}},
        ]
        with patch('probe_client.time.sleep'):
            self.assertEqual(saved_message(client, {'subject': 'fixture'}), {'id': 2})
        self.assertEqual(
            client.call.call_args_list,
            [call('save', {'details': {'subject': 'fixture'}})],
        )
        self.assertEqual(client.command.call_count, 3)
        client.record.assert_called_once_with(
            'save_response_fixture', {'mode': 'draft', 'messages': []}
        )

    def test_ambiguous_saved_message_is_not_guessed_or_saved_again(self):
        client = Mock()
        client.call.return_value = {'mode': 'draft', 'messages': []}
        client.command.side_effect = [
            {'ok': True, 'result': {'messages': []}},
            {'ok': True, 'result': {'messages': [{'id': 1}, {'id': 2}]}},
        ]
        with (
            patch('probe_client.time.monotonic', side_effect=[0, 31]),
            patch('probe_client.time.sleep'),
        ):
            with self.assertRaisesRegex(AssertionError, 'did not become queryable'):
                saved_message(client, {'subject': 'fixture'})
        self.assertEqual(client.call.call_count, 1)

    def test_query_polls_until_stored_body_matches_without_mutation(self):
        client = Mock()
        client.command.side_effect = [
            {'ok': True, 'result': {'messages': []}},
            {'ok': True, 'result': {'messages': [{'id': 5}]}},
            {
                'ok': True,
                'result': {
                    'header': {'id': 5},
                    'full': {'parts': [{'body': 'updated body'}]},
                },
            },
        ]
        with patch('probe_client.time.sleep'):
            self.assertEqual(
                wait_query(client, 'fixture', 1, body='updated body'), [{'id': 5}]
            )
        client.call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
