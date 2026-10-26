from pathlib import Path

from automation.paths import REPOSITORY_ROOT


def read_lcov(path):
    files = {}
    current = None
    for line in path.read_text().splitlines():
        if line.startswith('SF:'):
            source = Path(line[3:])
            if not source.is_absolute():
                source = REPOSITORY_ROOT / source
            current = files.setdefault(source.resolve(), {})
        elif line.startswith('DA:') and current is not None:
            number, hits = line[3:].split(',')[:2]
            current[int(number)] = max(current.get(int(number), 0), int(hits))
    return files


def merge(reports):
    merged = {}
    for report in reports:
        for source, lines in read_lcov(report).items():
            target = merged.setdefault(source, {})
            for number, hits in lines.items():
                target[number] = max(target.get(number, 0), hits)
    return merged


def summary(merged):
    rows = []
    total = covered = 0
    for source, lines in sorted(merged.items()):
        if not lines or not source.is_relative_to(REPOSITORY_ROOT):
            continue
        hit = sum(1 for hits in lines.values() if hits > 0)
        total += len(lines)
        covered += hit
        relative = source.relative_to(REPOSITORY_ROOT)
        rows.append(
            f'{100 * hit / len(lines):6.1f}%  {hit:5}/{len(lines):<5}  {relative}'
        )
    if total:
        rows.append(f'{100 * covered / total:6.1f}%  {covered:5}/{total:<5}  total')
    return rows
