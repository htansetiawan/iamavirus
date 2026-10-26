"""Mirror data/raw to the archive drive as gzip tarballs.

    python tools/mirror_raw.py [--raw data/raw] [--store {storage}/iamavirus-data/raw-archive]

--store defaults to $STORE/raw-archive; the drive path is per machine.

The drive is exFAT with 128 KB clusters, where the replay tree (hundreds of
thousands of small files) takes about 15 times its size and a file-by-file
sync spends most of an hour on metadata. So the mirror is append-only:

    base-<stamp>.tar.gz    all of data/raw, written once
    daily-<stamp>.tar.gz   the games accepted since the previous archive, with
                           accepted.jsonl and the new leaderboard snapshots
    mirror-state.json      how many accepted.jsonl lines are archived

Restore: extract the base, then every daily archive in order, into data/raw.
"""
from __future__ import annotations

import argparse
import json
import os
import tarfile
import time


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    store = os.environ.get("STORE")
    ap.add_argument("--store", default=f"{store}/raw-archive" if store else None, required=not store,
                    help="archive directory (default $STORE/raw-archive)")
    args = ap.parse_args()
    os.makedirs(args.store, exist_ok=True)
    state_path = os.path.join(args.store, "mirror-state.json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    stamp = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
    with open(os.path.join(args.raw, "accepted.jsonl")) as f:
        lines = f.readlines()
    snapshots = sorted(os.listdir(os.path.join(args.raw, "snapshots")))
    if "lines" not in state:
        out = os.path.join(args.store, f"base-{stamp}.tar.gz")
        with tarfile.open(out + ".part", "w:gz", compresslevel=6) as tar:
            tar.add(args.raw, arcname=".")
        games = len(lines)
    else:
        ids = []
        for line in lines[state["lines"]:]:
            try:
                ids.append(json.loads(line)["id"])
            except (ValueError, KeyError):
                continue
        new_snaps = [s for s in snapshots if s > state.get("last_snapshot", "")]
        if not ids and not new_snaps:
            print("mirror: nothing new")
            return
        out = os.path.join(args.store, f"daily-{stamp}.tar.gz")
        with tarfile.open(out + ".part", "w:gz", compresslevel=6) as tar:
            for gid in ids:
                path = os.path.join(args.raw, "games", gid)
                if os.path.isdir(path):
                    tar.add(path, arcname=f"games/{gid}")
            for s in new_snaps:
                tar.add(os.path.join(args.raw, "snapshots", s), arcname=f"snapshots/{s}")
            tar.add(os.path.join(args.raw, "accepted.jsonl"), arcname="accepted.jsonl")
            quarantine = os.path.join(args.raw, "quarantine")
            if os.path.isdir(quarantine):
                tar.add(quarantine, arcname="quarantine")
        games = len(ids)
    os.replace(out + ".part", out)
    state = {"lines": len(lines), "last_snapshot": snapshots[-1] if snapshots else "", "last_archive": os.path.basename(out)}
    json.dump(state, open(state_path, "w"), indent=1)
    print(f"mirror: {os.path.basename(out)} ({games} games, {os.path.getsize(out) / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
