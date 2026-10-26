#!/usr/bin/env python3
"""Build an isolated v35-derived leaf-depth experiment; never edit shared mist-c."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.archive) as archive:
        archive.extractall(root)
    path = root / 'src/sfeval.c'
    original = path.read_text()
    anchor = 'static int n_workers = 0, restarts = 0, multipv_set = 256;'
    init = '    snprintf(engine_path, sizeof engine_path, "%s", path);'
    command = '    snprintf(cmd, sizeof cmd, "position fen %s\\ngo depth 1\\n", fen);'
    for text in (anchor, init, command):
        if original.count(text) != 1:
            raise RuntimeError('Source contract mismatch; expected immutable v35 sfeval.c')
    changed = original.replace(anchor, anchor + '\nstatic int leaf_depth = 1;')
    changed = changed.replace(init, '''    /* Experiment only: default matches the released evaluator. Invalid or
     * excessive depths fall back to 1; the game clock/search budget is unchanged. */
    const char *depth_env = getenv("MIST_SF_DEPTH");
    char *depth_end = NULL;
    long requested = depth_env ? strtol(depth_env, &depth_end, 10) : 1;
    leaf_depth = depth_env && (*depth_env == '\\0' || !depth_end || *depth_end ||
                              requested < 1 || requested > 4) ? 1 : (int)requested;
''' + init)
    changed = changed.replace(command,
        '    snprintf(cmd, sizeof cmd, "position fen %s\\ngo depth %d\\n", fen, leaf_depth);')
    path.write_text(changed)
    subprocess.run(['bash', 'build.sh'], cwd=root, check=True)
    receipt = {
        'classification': 'experimental build; not an arena release or strength result',
        'parent_archive': str(args.archive.resolve()), 'parent_sha256': digest(args.archive),
        'source_changes': {'src/sfeval.c': {
            'before': hashlib.sha256(original.encode()).hexdigest(), 'after': digest(path)}},
        'binary_sha256': digest(root / 'mist'),
        'stockfish_sha256': digest(root / 'bin/stockfish'),
        'history_sha256': digest(root / 'data/history.bin'),
        'setting': 'MIST_SF_DEPTH=1|3 (default 1; implementation accepts 1..4)',
        'held_fixed': ['belief', 'move model', 'history table', 'guards', 'CFR', 'clock', 'MultiPV'],
    }
    (root / 'experiment.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
