import copy
import json
import tempfile
import unittest
from pathlib import Path

from raicho_protocol_schema import validate_sources

ROOT = Path(__file__).resolve().parent.parent


class ProtocolGenerationTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(
            (ROOT / 'protocol/schema/connector.schema.json').read_text()
        )
        self.limits = json.loads((ROOT / 'protocol/limits.json').read_text())

    def test_canonical_sources_are_consistent(self):
        validate_sources(self.schema, self.limits)

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
                    validate_sources(schema, self.limits)

    def test_unknown_vocabulary_is_rejected(self):
        self.schema['unevaluatedProperties'] = False
        with self.assertRaisesRegex(ValueError, 'vocabulary'):
            validate_sources(self.schema, self.limits)

    def test_schema_and_runtime_limits_cannot_drift(self):
        for name in [
            'protocol_version',
            'heartbeat_interval_ms',
            'heartbeat_timeout_ms',
        ]:
            with self.subTest(name=name):
                limits = self.limits | {name: self.limits[name] + 1}
                with self.assertRaisesRegex(ValueError, 'disagrees'):
                    validate_sources(self.schema, limits)

    def test_limits_must_be_positive_integers(self):
        for value in [0, -1, True, 1.5, '4096']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_sources(
                        self.schema, self.limits | {'authentication_max_bytes': value}
                    )

    def test_generated_output_tampering_is_detected(self):
        from raicho_protocol import changed_outputs

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            generated = root / 'generated'
            committed = root / 'committed'
            generated.mkdir()
            committed.mkdir()
            (generated / 'contract.ts').write_text('expected\n')
            self.assertEqual(
                changed_outputs(generated, committed, ['contract.ts']), ['contract.ts']
            )
            (committed / 'contract.ts').write_text('expected\n')
            self.assertEqual(changed_outputs(generated, committed, ['contract.ts']), [])
            (committed / 'contract.ts').write_text('edited\n')
            self.assertEqual(
                changed_outputs(generated, committed, ['contract.ts']), ['contract.ts']
            )
