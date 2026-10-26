import copy
import json
import tempfile
import unittest
from pathlib import Path

from protocol.generator.cli import ROOT, changed_outputs
from protocol.generator.validation import validate_sources, validate_status


class ProtocolGenerationTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / 'protocol/schema/connector.schema.json').read_text())
        self.limits = json.loads((ROOT / 'protocol/limits.json').read_text())
        self.diagnostics = json.loads((ROOT / 'protocol/diagnostics.json').read_text())
        self.status = json.loads((ROOT / 'protocol/schema/status.schema.json').read_text())

    def test_canonical_sources_are_consistent(self):
        validate_sources(self.schema, self.limits, self.diagnostics)
        validate_status(self.status, self.diagnostics)

    def test_status_schema_cannot_drift_from_diagnostics(self):
        for name in ['BackendState', 'BackendError']:
            with self.subTest(definition=name):
                status = copy.deepcopy(self.status)
                status['definitions'][name]['enum'].append('private_detail')
                with self.assertRaisesRegex(ValueError, 'disagrees'):
                    validate_status(status, self.diagnostics)
        status = copy.deepcopy(self.status)
        status['definitions']['Label']['format'] = 'uri'
        with self.assertRaisesRegex(ValueError, 'vocabulary'):
            validate_status(status, self.diagnostics)

    def test_remote_file_and_missing_references_are_rejected(self):
        for reference in [
            'https://example.test/schema.json',
            'file:///tmp/schema.json',
            '../schema.json',
            '#/definitions/Missing',
        ]:
            with self.subTest(reference=reference):
                schema = copy.deepcopy(self.schema)
                schema['oneOf'][0]['$ref'] = reference
                with self.assertRaises(ValueError):
                    validate_sources(schema, self.limits, self.diagnostics)

    def test_unknown_vocabulary_is_rejected(self):
        self.schema['unevaluatedProperties'] = False
        with self.assertRaisesRegex(ValueError, 'vocabulary'):
            validate_sources(self.schema, self.limits, self.diagnostics)

    def test_schema_and_runtime_protocol_versions_cannot_drift(self):
        limits = self.limits | {'protocol_version': self.limits['protocol_version'] + 1}
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            validate_sources(self.schema, limits, self.diagnostics)

    def test_json_depth_stays_below_the_parser_limits(self):
        with self.assertRaisesRegex(ValueError, 'depth'):
            validate_sources(self.schema, self.limits | {'maximum_json_depth': 101}, self.diagnostics)

    def test_limits_must_be_positive_integers(self):
        for value in [0, -1, True, 1.5, '4096']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_sources(
                        self.schema,
                        self.limits | {'maximum_authentication_bytes': value},
                        self.diagnostics,
                    )

    def test_diagnostics_must_be_unique_codes_covering_protocol_errors(self):
        for diagnostics in [
            self.diagnostics | {'backend_states': []},
            self.diagnostics | {'backend_states': ['connected', 'connected']},
            self.diagnostics | {'backend_errors': ['Invalid-Code']},
            self.diagnostics | {'backend_errors': ['storage_unavailable']},
            self.diagnostics | {'contract_errors': ['storage_unavailable']},
            self.diagnostics | {'contract_errors': []},
            {'backend_states': ['connected']},
        ]:
            with self.subTest(diagnostics=diagnostics):
                with self.assertRaises(ValueError):
                    validate_sources(self.schema, self.limits, diagnostics)

    def test_generated_output_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            generated = root / 'generated'
            committed = root / 'committed'
            generated.mkdir()
            committed.mkdir()
            (generated / 'contract.ts').write_text('expected\n')
            self.assertEqual(changed_outputs(generated, committed, ['contract.ts']), ['contract.ts'])
            (committed / 'contract.ts').write_text('expected\n')
            self.assertEqual(changed_outputs(generated, committed, ['contract.ts']), [])
            (committed / 'contract.ts').write_text('edited\n')
            self.assertEqual(changed_outputs(generated, committed, ['contract.ts']), ['contract.ts'])
