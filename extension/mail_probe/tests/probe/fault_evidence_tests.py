import unittest

from scenario_faults import verify_fault_events


class FaultEvidenceTests(unittest.TestCase):
    def test_missing_injected_failure_cannot_pass(self):
        with self.assertRaises(AssertionError):
            verify_fault_events(
                {}, {'smtp_accepted': 1}, accepted=1, required=['smtp_ack_dropped']
            )

    def test_duplicate_submission_cannot_pass(self):
        with self.assertRaises(AssertionError):
            verify_fault_events(
                {'smtp_accepted': 3},
                {'smtp_accepted': 5, 'smtp_ack_dropped': 1},
                accepted=1,
                required=['smtp_ack_dropped'],
            )

    def test_copy_retries_do_not_count_as_duplicate_submission(self):
        delta = verify_fault_events(
            {'smtp_accepted': 2, 'sent_append_rejected': 1},
            {'smtp_accepted': 3, 'sent_append_rejected': 4},
            accepted=1,
            required=['sent_append_rejected'],
        )
        self.assertEqual(delta, {'smtp_accepted': 1, 'sent_append_rejected': 3})

    def test_rejection_requires_no_upstream_acceptance(self):
        with self.assertRaises(AssertionError):
            verify_fault_events(
                {},
                {'smtp_accepted': 1, 'smtp_rejected': 1},
                accepted=0,
                required=['smtp_rejected'],
            )

    def test_counter_reset_is_not_valid_evidence(self):
        with self.assertRaises(AssertionError):
            verify_fault_events({'smtp_accepted': 2}, {}, accepted=0)


if __name__ == '__main__':
    unittest.main()
