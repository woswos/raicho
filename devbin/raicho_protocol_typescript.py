import os
import shutil
import subprocess
import tempfile


def test_typescript(root):
    source = root / 'protocol/typescript'
    with tempfile.TemporaryDirectory(prefix='raicho-protocol-typescript-') as directory:
        subprocess.run(
            ['tsc', '--project', str(source / 'tsconfig.json'), '--outDir', directory],
            cwd=root,
            check=True,
        )
        shutil.copyfile(source / 'package.json', f'{directory}/package.json')
        tests = sorted(str(path) for path in (source / 'tests').glob('*.test.mjs'))
        if not tests:
            raise ValueError('No TypeScript protocol tests were found.')
        subprocess.run(
            ['node', '--test', *tests],
            cwd=root,
            env=os.environ | {'RAICHO_PROTOCOL_BUILD_DIR': directory},
            check=True,
        )
