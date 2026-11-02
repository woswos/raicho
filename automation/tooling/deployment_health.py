import json
import subprocess
import sys


def row(label, value):
    return f'  {label:<18} {value}'


def short(commit):
    revision, dirty, _ = commit.partition('-dirty')
    return revision[:7] + dirty


def commits_behind(deployed, checkout, directory=None):
    revisions = [commit.removesuffix('-dirty') for commit in (deployed, checkout)]
    result = subprocess.run(
        ['git', 'rev-list', '--count', f'{revisions[0]}..{revisions[1]}'],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    return int(result.stdout) if result.returncode == 0 else None


def connector(backend):
    error = f', last error {backend["last_error"]}' if backend['last_error'] else ''
    return f'{backend["status"]}{error}, {backend["heartbeat_count"]} heartbeats'


def deployed_commit(deployed, checkout, behind):
    if not deployed:
        return 'unknown'
    if deployed == checkout:
        return f'{short(deployed)}, matches the checkout'
    if behind:
        return f'{short(deployed)}, {behind} commits behind checkout {short(checkout)}'
    return f'{short(deployed)}, checkout is {short(checkout)}'


def report(status, checkout, behind=None):
    database = status['database']
    healthy = status['status'] == 'ready' and status['backend']['status'] == 'connected'
    lines = [
        row('Raicho', f'{status["status"]}, version {status["version"]}'),
        row('Database', f'{database["status"]}, {database["engine"]} {database["version"]}'),
        row('Connector', connector(status['backend'])),
        row('Deployed commit', deployed_commit(status['commit'], checkout, behind)),
        row('Health', 'healthy' if healthy else 'not healthy'),
    ]
    return lines, healthy


def main(arguments):
    checkout = arguments[0]
    text = sys.stdin.read()
    if not text.strip():
        print('Raicho did not answer. Run make deploy-ps to check that it runs.', file=sys.stderr)
        return 1
    try:
        status = json.loads(text)
    except json.JSONDecodeError:
        print('Raicho returned an unexpected status response.', file=sys.stderr)
        return 1
    deployed = status['commit']
    behind = commits_behind(deployed, checkout) if deployed and deployed != checkout else None
    lines, healthy = report(status, checkout, behind)
    print('\n'.join(lines))
    return 0 if healthy else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
