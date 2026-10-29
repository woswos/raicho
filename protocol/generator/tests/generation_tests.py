import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protocol.generator import cli
from protocol.generator.cli import NODE_REPORTER, ROOT, node_reporter, sync_outputs
from protocol.generator.validation import validate_sources, validate_status


class Stop(Exception):
    pass


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

    def test_the_wire_integer_limit_bounds_sequences_and_other_limits(self):
        cases = [
            (self.limits['maximum_wire_integer'] - 1, 'Protocol schema disagrees with limit maximum_wire_integer.'),
            (2**31, 'maximum_wire_integer must not exceed 2147483647.'),
            (60000, 'Protocol limits maximum_control_bytes must not exceed maximum_wire_integer.'),
        ]
        for value, message in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as raised:
                    validate_sources(self.schema, self.limits | {'maximum_wire_integer': value}, self.diagnostics)
                self.assertEqual(str(raised.exception), message)

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

    def test_outputs_sync_only_generated_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary) / 'staging'
            root = Path(temporary) / 'root'
            for language in cli.DESTINATIONS:
                (staging / language).mkdir(parents=True)
            destination = cli.DESTINATIONS['typescript']
            committed = root / destination
            committed.mkdir(parents=True)
            (staging / 'typescript/contract_generated.ts').write_text('expected\n')
            (committed / 'old_generated.ts').write_text('stale\n')
            (committed / 'app.ts').write_text('hand-written\n')
            (committed / '.contract_generated.ts.swp').write_text('editor\n')
            (committed / 'contract_generated.ts~').write_text('backup\n')
            (committed / 'folder_generated.ts').mkdir()
            expected = [str(destination / 'contract_generated.ts'), str(destination / 'old_generated.ts')]
            self.assertEqual(sync_outputs(staging, root, 'check'), expected)
            self.assertTrue((committed / 'old_generated.ts').exists())
            self.assertEqual(sync_outputs(staging, root, 'generate'), expected)
            self.assertEqual(
                sorted(path.name for path in committed.iterdir()),
                [
                    '.contract_generated.ts.swp',
                    'app.ts',
                    'contract_generated.ts',
                    'contract_generated.ts~',
                    'folder_generated.ts',
                ],
            )
            self.assertEqual(sync_outputs(staging, root, 'check'), [])
            (committed / 'contract_generated.ts').write_text('edited\n')
            self.assertEqual(sync_outputs(staging, root, 'check'), [str(destination / 'contract_generated.ts')])
            (staging / 'typescript/contract_generated.ts').write_text('expected\n')
            (staging / 'web/notes.ts').write_text('')
            with self.assertRaisesRegex(ValueError, 'notes.ts'):
                sync_outputs(staging, root, 'generate')
            self.assertEqual((committed / 'contract_generated.ts').read_text(), 'edited\n')
            self.assertFalse((root / cli.DESTINATIONS['web'] / 'notes.ts').exists())

    def test_verbose_protocol_tests_use_the_standard_reporter(self):
        for verbose, reporter in (('', NODE_REPORTER), ('1', '--test-reporter=spec')):
            with self.subTest(verbose=verbose), mock.patch.dict(os.environ, {'VERBOSE': verbose}):
                self.assertEqual(node_reporter(), reporter)

    def test_the_generator_runs_from_the_shared_target_directory(self):
        builds = {
            'check': ['cargo', 'build', '--workspace', '--all-targets', '--locked'],
            'generate': ['cargo', 'build', '--locked', '--package', 'raicho-protocol-generator'],
        }
        for action, build in builds.items():
            with (
                self.subTest(action=action),
                mock.patch.dict(os.environ, {'CARGO_TARGET_DIR': '/cache/target'}),
                mock.patch.object(cli.subprocess, 'run', side_effect=[None, None, Stop()]) as run,
                self.assertRaises(Stop),
            ):
                cli.generate(action)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual(commands[0], build)
            self.assertEqual(commands[1][0], '/cache/target/debug/raicho-protocol-generator')
            self.assertEqual(commands[2][0], 'node')
