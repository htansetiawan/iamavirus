"""Independent decoded scan against the original293 feature-stream checksum."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'astra-submissions/analysis/ragged-train-20261110'
sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
import numpy as np
from prior_training_cache import PriorCache
from reconstructed_cache import Cache, fields, FATAL, CAPTURE, SELECTED


def main():
    started = time.monotonic()
    plan = json.loads((OUT / 'plan.json').read_text())
    os.sched_setaffinity(0, set(plan['cores']))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('600s independent scan bound')))
    signal.alarm(plan['max_seconds'])
    prior = PriorCache(plan['destination'])
    world = Cache(plan['state_cache'])
    original = json.loads(Path(plan['original_receipt']).read_text())
    digest = hashlib.sha256(); cursor = 0; capture = fatal = 0
    # Deliberately reconstruct the old stream here, without exporter or its
    # update_digest function, original native library, model or inference.
    for number in range(prior.manifest['contexts']):
        context, values = prior.record(number)
        start, record_index, total, target, count, game_index, selection, flags = context
        assert start == cursor
        game = world.games[game_index]
        assert game['start'] <= record_index < game['start'] + game['moves']
        assert record_index - game['start'] in game['selected_plies']
        row = fields(world.record(record_index))
        assert (row[8], row[9]) == (selection, flags) and selection & SELECTED
        assert int(values['move'][target]) == row[7]
        assert bool(values['x'][target, 0]) == bool(flags & CAPTURE)
        assert bool(values['x'][target, 22]) == bool(flags & FATAL)
        assert not values['reserved'].any()
        assert int(values['history'].sum()) <= total
        digest.update(np.array(values['x'], dtype='<f4', order='C').tobytes())
        digest.update(np.array(values['base'], dtype='<f4', order='C').tobytes())
        digest.update(np.array(values['history'], dtype='<u4', order='C').tobytes())
        digest.update(np.array([target, total], dtype='<i8').tobytes())
        cursor += count; capture += bool(flags & CAPTURE); fatal += bool(flags & FATAL)
    assert cursor == prior.manifest['candidates']
    assert prior.manifest['contexts'] == original['decisions'] == 92940
    assert digest.hexdigest() == prior.manifest['unpacked_sha256'] == original['unpacked_sha256']
    assert (capture, fatal) == (prior.manifest['capture_targets'], prior.manifest['fatal_targets'])
    result = dict(passed=True, contexts=prior.manifest['contexts'], candidates=cursor,
                  decoded_original_sha256=digest.hexdigest(), capture_targets=capture, fatal_targets=fatal,
                  seconds=time.monotonic()-started, no_model_or_native_inference=True,
                  scope='Original TRAIN round-trip and selection/label integrity; no predictive or strength test.')
    with (OUT / 'independent-review.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    world.close()
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
