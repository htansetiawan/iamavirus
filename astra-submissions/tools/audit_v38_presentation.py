"""Read-only inventory of the immutable arena-v38 archive for human review.

Counts are derived from the ZIP and its manifest, not from the moving engine
checkout. This does not run Stockfish, fit a model, query the API or play games.
"""
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    manifest_path = ROOT / 'astra-submissions/v38-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    archive = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    with archive.open('rb') as stream:
        archive_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert archive_sha == manifest['archive_sha256']
    with zipfile.ZipFile(archive) as zipped:
        expected = manifest['source_sha256']
        for name, sha in expected.items():
            assert digest(zipped.read(name)) == sha, name
        history = zipped.read('data/history.bin')
        magic, version, count = struct.unpack_from('<8sII', history)
        assert magic == b'MISTHIST' and version == 1
        assert len(history) == 16 + count * 16
        rows = list(struct.iter_unpack('<QII', history[16:]))
        assert len(rows) == count
        assert len({(h, m) for h, m, c in rows}) == count
        assert all(c > 0 for h, m, c in rows)
        assert all(a[0] <= b[0] for a, b in zip(rows, rows[1:]))
        grouped = Counter()
        for h, m, c in rows:
            grouped[h] += 1
        model_source = zipped.read('src/movemodel.c').decode()
        coefficients = {}
        for kind in ('full', 'cheap'):
            found = re.search(r'theta_' + kind + r'\[MM_FEATURES\]\s*=\s*\{([^}]+)\}', model_source)
            assert found
            values = [float(v.strip().rstrip('f')) for v in found.group(1).split(',')]
            assert len(values) == 28
            coefficients[kind] = dict(count=len(values), nonzero=sum(v != 0 for v in values), values=values)
        cfr_header = zipped.read('src/cfr.h').decode()
        assert 'double *regret, *last, *strategy, *strategy_sum;' in cfr_header
        belief_source = zipped.read('src/belief.c').decode()
        assert '(void)hist; return position_key(p);' in belief_source
        search_source = zipped.read('src/gtcfr.c').decode()
        assert 'game_init(&t.g)' in search_source and 'game_free(&t.g)' in search_source
        assert 'if (x[o + a] > x[o + best]) best = a;' in search_source
        launcher = zipped.read('run.sh').decode()
        assert 'export ASTRA_SF_ALLCHILDREN=1' in launcher
        source_names = ('src/belief.c', 'src/belief.h', 'src/cfr.c', 'src/cfr.h',
                        'src/gtcfr.c', 'src/main.c', 'src/movemodel.c', 'src/movemodel.h',
                        'src/front.h', 'src/sfeval.c', 'third_party/stockfish19/astra-allchildren.patch')
        return dict(
            at=datetime.now(timezone.utc).isoformat(), archive=str(archive.relative_to(ROOT)),
            archive_sha256=archive_sha, manifest_sha256=digest(manifest_path.read_bytes()),
            manifest_member_hashes_verified=len(expected), zip_members=len(zipped.infolist()),
            history=dict(file='data/history.bin', sha256=digest(history), bytes=len(history),
                         header_bytes=16, record_bytes=16, records=count,
                         distinct_history_hashes=len(grouped), total_recorded_move_counts=sum(c for h, m, c in rows),
                         maximum_distinct_moves_per_history_hash=max(grouped.values()),
                         sorted_by_history_hash=True, unique_history_move_pairs=True,
                         meaning='Each row is a 64-bit history hash, encoded move and empirical count. '
                                 'Hash-key count is not a count of complete games or collision-free full histories.'),
            move_model=dict(coefficient_vectors=coefficients,
                            source_recorded_fit='148,357 games, 9,901,850 moves, September 1–October 31; '
                                                '26,029 held-out games, 1,734,620 moves. '
                                                'Read from archived source; not independently reconstructed by this audit.'),
            solver=dict(per_information_set_action_arrays=['regret', 'last', 'strategy', 'strategy_sum'],
                        array_count=4, entries='sum of action counts across current information sets, variable per decision',
                        tree_carried_between_moves=False, final_action='maximum-probability current action'),
            behavior_checks=dict(board_only_belief_merge=True, all_child_scorer_enabled=True),
            source_sha256={name: digest(zipped.read(name)) for name in source_names},
            scope='Read-only archive/hash/structure/count audit. Does not verify the arena server ZIP hash, '
                  'training population, exact posterior correctness, equilibrium guarantees or playing strength.')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as stream:
            stream.write(payload)
    print(json.dumps({key: result[key] for key in ('archive_sha256', 'manifest_member_hashes_verified', 'zip_members', 'history')}, indent=2))
