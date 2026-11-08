#!/usr/bin/env python3
"""Fail before publishing reports when their mounted raw archive is unavailable."""
import argparse
from pathlib import Path


def check_raw_available(raw: Path, reports: bool = False) -> None:
    # Ingest may bootstrap an ordinary local directory, but must never treat a
    # disconnected archive symlink (including one in a parent) as an empty store.
    for path in (raw, *raw.parents, raw/'games', raw/'snapshots', raw/'accepted.jsonl'):
        if path.is_symlink() and not path.exists():
            raise OSError(f'raw archive link is unavailable: {path} -> {path.readlink()}')
    if raw.exists() and not raw.is_dir():
        raise OSError(f'raw archive is not a directory: {raw}')
    if reports:
        for path in (raw, raw/'games', raw/'snapshots'):
            if not path.is_dir():
                raise OSError(f'report input directory is unavailable: {path}')
        journal = raw/'accepted.jsonl'
        if not journal.is_file() or journal.stat().st_size == 0:
            raise OSError(f'accepted-game index is missing or empty: {journal}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=Path('data/raw'))
    parser.add_argument('--reports', action='store_true')
    args = parser.parse_args()
    try:
        check_raw_available(args.raw, args.reports)
    except OSError as exc:
        parser.exit(1, f'{exc}; preserve the last good reports\n')


if __name__ == '__main__':
    main()
