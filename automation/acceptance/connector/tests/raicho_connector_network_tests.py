import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / 'raicho_check_connector.bash'


class ConnectorNetworkTests(unittest.TestCase):
    def test_uses_docker_selected_subnet_and_compose_ownership_labels(self):
        function = re.search(
            r'^prepare_network\(\) \{\n.*?^\}',
            RUNNER.read_text(),
            re.MULTILINE | re.DOTALL,
        ).group()
        for subnet in ('10.173.0.0/16', '172.29.64.0/20'):
            with (
                self.subTest(subnet=subnet),
                tempfile.TemporaryDirectory() as temporary,
            ):
                directory = Path(temporary)
                trace = directory / 'trace'
                docker = directory / 'docker'
                docker.write_text(
                    '#!/usr/bin/env python3\n'
                    'import json, os, sys\n'
                    'with open(os.environ["MOCK_TRACE"], "a") as output:\n'
                    '    output.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                    'if sys.argv[1:3] == ["network", "inspect"]:\n'
                    '    print(os.environ["MOCK_SUBNET"])\n'
                )
                docker.chmod(0o700)
                subprocess.run(
                    ['bash', '-euo', 'pipefail', '-c', function + '\nprepare_network'],
                    env={
                        **os.environ,
                        'PATH': f'{directory}:{os.environ["PATH"]}',
                        'RAICHO_PROJECT': 'raicho-connector-network-test',
                        'MOCK_TRACE': str(trace),
                        'MOCK_SUBNET': subnet,
                    },
                    check=True,
                    capture_output=True,
                    text=True,
                )
                commands = [json.loads(line) for line in trace.read_text().splitlines()]
                creations = [
                    command
                    for command in commands
                    if command[:2] == ['network', 'create']
                ]
                self.assertEqual(len(creations), 2)
                self.assertNotIn('--subnet', creations[0])
                self.assertEqual(
                    creations[1][creations[1].index('--subnet') + 1], subnet
                )
                for command in creations:
                    self.assertIn(
                        'com.docker.compose.project=raicho-connector-network-test',
                        command,
                    )
                    self.assertIn('com.docker.compose.network=application', command)
