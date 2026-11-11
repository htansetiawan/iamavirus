"""Stage and exercise an isolated importer fix on two verified real seats.

The shared importer is untouched. This changes unknown attribution, never
rules, moves, outcomes, old accepted files or existing split assignments.
"""
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import _native, ingest

NAME = 'corpus-attribution-fix-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STAGE = ROOT / 'astra-submissions/experiments' / NAME
VALIDATOR = ROOT / 'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def main():
    OUT.mkdir(exist_ok=False)
    STAGE.mkdir(exist_ok=False)
    original_path = ROOT / 'learning/ingest.py'
    original_bytes = original_path.read_bytes()
    old = original_bytes.decode()
    before = '''        white = opponent.replace("_", " ") if side == "b" else "IAmAVirus"
        black = "IAmAVirus" if side == "b" else opponent.replace("_", " ")
        replay = replay_from_moves(game_id, moves, result, reason_text, white, black)
        replay["whitePlayerId"] = white
        replay["blackPlayerId"] = black
        replay["source"] = "corpus"
'''
    after = '''        # The corpus records an arbitrary selected seat, not our team.
        # Its player name/ID and the opponent ID are absent from this format.
        unknown = "Unknown corpus seat"
        white = opponent.replace("_", " ") if side == "b" else unknown
        black = unknown if side == "b" else opponent.replace("_", " ")
        replay = replay_from_moves(game_id, moves, result, reason_text, white, black)
        replay["whitePlayerId"] = None
        replay["blackPlayerId"] = None
        replay["source"] = "corpus"
        replay["corpusSeat"] = side
'''
    assert old.count(before) == 1
    fixed_source = old.replace(before, after)
    fixed_path = STAGE / 'ingest.py'
    fixed_path.write_text(fixed_source)
    patch = ''.join(difflib.unified_diff(old.splitlines(True), fixed_source.splitlines(True),
                                         fromfile='a/learning/ingest.py', tofile='b/learning/ingest.py'))
    (OUT / 'ingest-attribution.patch').write_text(patch)
    module_name = 'learning._astra_corpus_attribution_fixed'
    spec = importlib.util.spec_from_file_location(module_name, fixed_path)
    fixed = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = fixed
    spec.loader.exec_module(fixed)
    assert sha(VALIDATOR) == 'ae7a39913fe9d058b4b5392849ffc6a9260d2123a891d12454b016b4843665e3'
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    selected_ids = ['13r3tgga', '1b8luqb3']
    corpus_path = ROOT / 'corpus/corpus-all.txt'
    lines = {line.split()[0]: line for line in corpus_path.read_text().splitlines() if line.strip()}
    verified = load(ROOT / 'data/astra-spool/corpus-metadata-recovery-20261111/supplement.json')
    true_teams = {r['id']: r['metadata'] for r in verified}
    rows = []
    with tempfile.TemporaryDirectory(prefix='iamavirus-corpus-attribution-') as temporary:
        base = Path(temporary)
        fixture = base / 'corpus.txt'
        fixture.write_text(''.join(lines[game] + '\n' for game in selected_ids))
        old_store, new_store = base / 'old', base / 'new'
        old_counts = ingest.ingest_from_corpus(old_store, fixture)
        new_counts = fixed.ingest_from_corpus(new_store, fixture)
        assert old_counts == new_counts == dict(accepted=2, quarantined=0, skipped=0, recovered=0)
        for game in selected_ids:
            side_token = lines[game].split()[1]
            side = 'white' if side_token == 'w' else 'black'
            other = 'black' if side == 'white' else 'white'
            original = load(old_store / 'games' / game / 'replay.json')
            corrected = load(new_store / 'games' / game / 'replay.json')
            assert original[side] == 'IAmAVirus' and true_teams[game][side] != 'IAmAVirus'
            assert corrected[side] == 'Unknown corpus seat'
            assert corrected[other] == original[other] == true_teams[game][other]
            assert corrected['whitePlayerId'] is corrected['blackPlayerId'] is None
            assert corrected['corpusSeat'] == side_token
            excluded = {'white', 'black', 'whitePlayerId', 'blackPlayerId', 'corpusSeat'}
            assert {k: v for k, v in corrected.items() if k not in excluded} == {
                k: v for k, v in original.items() if k not in excluded}
            rows.append(dict(game=game, side=side, actual_team=true_teams[game][side],
                             old_label=original[side], corrected_label=corrected[side],
                             frames_unchanged=len(corrected['frames'])))
        paths = list(old_store.rglob('*'))
        old_hashes = {str(p.relative_to(old_store)): sha(p) for p in paths if p.is_file()}
        skipped = fixed.ingest_from_corpus(old_store, fixture)
        assert skipped == dict(accepted=0, quarantined=0, skipped=2, recovered=0)
        assert old_hashes == {str(p.relative_to(old_store)): sha(p) for p in paths if p.is_file()}
    assert original_path.read_bytes() == original_bytes
    result = dict(at=datetime.now(timezone.utc).isoformat(), status='passed', real_seats=rows,
                  shared_source_unchanged=True, old_cache_not_rewritten=True,
                  current_raw_or_generations_changed=False,
                  hashes={str(p): sha(p) for p in (original_path, fixed_path, OUT / 'ingest-attribution.patch',
                                                  VALIDATOR, corpus_path, Path(__file__))},
                  scope='Two real source seats, both colors, exact full replay parity except attribution fields; existing-cache skip preserves bytes. Isolated importer patch only. No change to the shared importer or canonical records, no new split/export/model, network, GPU, game, commit, push or deployment.')
    with (OUT / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], cases=len(rows), shared_source_unchanged=True,
                          old_cache_not_rewritten=True)), flush=True)


if __name__ == '__main__':
    main()
