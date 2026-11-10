"""Verify the shipped cache reader and parity with the existing 4,000-game cache."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import sys
import time

import numpy as np

ROOT = Path.cwd()
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/'recovered-replay-cache-20261110'
STATE = ROOT/'data/astra-spool/recovered-replay-cache-20261110'
OLD = ROOT/'data/astra-spool/reconstructed-train-20261110'
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from reconstructed_cache import Cache, ROW, actor_events, decode_move, fields


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def array(cache, entry):
    start = entry['start']*ROW.size
    end = start+entry['records']*ROW.size
    return np.frombuffer(cache.data[start:end], dtype=np.uint8).reshape(-1,ROW.size)


def main():
    started = time.monotonic()
    status = json.loads((OUT/'execution.json').read_text())
    audited = json.loads((OUT/'independent-review.json').read_text())
    assert status['status']=='complete' and audited['passed']
    assert sha(STATE/'manifest.json')==audited['manifest_sha256']
    cache, previous = Cache(STATE), Cache(OLD)
    overlap_frames = 0
    try:
        groups = {entry['sequence_sha256']:entry for entry in cache.games}
        assert len(groups)==len(cache.games)==audited['counts']['accepted_groups']
        prior = {entry['sequence_sha256'] for entry in previous.games}
        excluded = {row["game"]:row for row in map(json.loads,(STATE/"excluded.jsonl").read_text().splitlines())}
        overlap_split = Counter()
        missing_legacy = Counter()
        for old in previous.games:
            row = groups.get(old['sequence_sha256'])
            if row is None:
                omitted = excluded[old['game']]
                assert omitted['sequence_sha256']==old['sequence_sha256']
                assert omitted['reason'] in ('technical_outcome','outcome_mismatch','illegal_move','continued_after_terminal')
                missing_legacy[omitted['reason']]+=1
                continue
            assert row['records']==old['records']
            x,y = array(cache,row),array(previous,old)
            assert np.array_equal(x[:,:62],y[:,:62]) and np.array_equal(x[:,63],y[:,63])
            assert np.array_equal(x[:,62],y[:,62]&4)
            overlap_split[row['split']]+=1
            overlap_frames+=row['records']
        exclusions = json.loads((ANALYSIS/'prospective-quiet-teacher-20261110/previous-exclusions.json').read_text())
        reused = {row['sequence_sha256'] for row in exclusions['games']}
        previously_used = Counter(row['split'] for digest,row in groups.items() if digest in reused)
        actor_checks = 0
        for split in ('train','validation','test'):
            entry = next(row for row in cache.games if row['split']==split)
            records = [cache.record(entry['start']+i) for i in range(entry['records'])]
            for side in (0,1):
                events=list(actor_events(records,side))
                assert len(events)==entry['records'] and not entry['clocks_available']
                for index,event in enumerate(events):
                    previous_action = fields(records[index-1]) if index else None
                    own_action = decode_move(previous_action[7]) if previous_action and previous_action[6]==side else None
                    assert event['known_own_action']==own_action and event['clocks'] is None
                    assert set(event)=={'ply','observation','known_own_action','clocks'}
                    actor_checks+=1
        assert sum(overlap_split.values())+sum(missing_legacy.values())==len(prior)==4000
        result=dict(cache_opened=True,overlap_groups=sum(overlap_split.values()),overlap_frames=overlap_frames,
            legacy_groups_excluded=dict(missing_legacy),
            overlap_by_new_split=dict(overlap_split),historical_exclusions_by_new_split=dict(previously_used),
            checked_actor_events=actor_checks,manifest_sha256=audited['manifest_sha256'],
            seconds=time.monotonic()-started,
            interpretation='Board, visibility, rule metadata, move and event flags match older validated cache. Selection keeps only the after-eight bit. Historical overlaps are counted so these partitions are used for future fits rather than scoring already-trained weights.')
        (OUT/'consumer-verification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)
    finally:
        previous.close()
        cache.close()

if __name__ == '__main__':
    main()
