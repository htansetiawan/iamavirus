"""Independent reduction of saved metadata responses; no HTTP or raw writes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
NAME = 'corpus-metadata-recovery-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def main():
    plan = load(OUT / 'plan.json')
    result = load(OUT / 'result.json')
    execution = load(OUT / 'execution.json')
    assert execution['status'] == 'completed' and execution['ended_at']
    for path, expected in {**plan['dependencies'], **result['hashes']}.items():
        assert digest(path) == expected, path
    sources = load(STORE / 'sources.json')
    payload = (STORE / 'receipts.jsonl').read_bytes()
    assert payload.endswith(b'\n')
    receipts = [json.loads(line) for line in payload.splitlines()]
    supplemental = load(STORE / 'supplement.json')
    supplement = {r['id']: r for r in supplemental}
    assert len(supplement) == len(supplemental) == result['recovered']
    assert [r['id'] for r in receipts] == [s['row']['id'] for s in sources[:len(receipts)]]
    assert len(receipts) == result['processed'] == execution['completed']
    assert result['remaining'] == len(sources) - len(supplement)
    assert Counter(r['status'] for r in receipts) == result['counts']
    fields = {'createdAt', 'whiteVersion', 'blackVersion', 'whitePlayerId',
              'blackPlayerId', 'white', 'black', 'rulesVersion', 'timeControl'}
    original_corpus = {}
    corpus = ROOT / 'corpus/corpus-all.txt'
    for line in corpus.read_text().splitlines():
        if line.strip():
            parts = line.split()
            assert parts[0] not in original_corpus
            original_corpus[parts[0]] = parts
    counts = Counter()
    corrections = []
    examples = []
    dates = []
    for source, receipt in zip(sources, receipts):
        row = source['row']
        game = row['id']
        assert digest(source['original_path']) == digest(source['canonical_path']) == source['sha256']
        original = load(source['original_path'])
        assert original['source'] == 'corpus' and not original.get('createdAt')
        parts = original_corpus[game]
        side = 'white' if parts[1] == 'w' else 'black'
        assert parts[1] in ('w', 'b') and original[side] == 'IAmAVirus'
        assert parts[2] == row['result']
        assert hashlib.sha256(' '.join(parts[5:]).encode()).hexdigest() == row['moves_sha256']
        if receipt['status'] != 'accepted':
            continue
        response = STORE / 'responses' / (game + '.json')
        assert receipt['response_path'] == str(response)
        assert digest(response) == receipt['fetch']['sha256'] == supplement[game]['response_sha256']
        assert receipt['fetch']['url'] == 'https://6s890.lids.mit.edu/api/games/' + game
        assert receipt['fetch']['status'] == 200 and 1 <= receipt['fetch']['attempts'] <= 5
        assert response.stat().st_size == receipt['response_bytes']
        replay = load(response)
        assert replay['id'] == row['id'] == original['id']
        assert replay['result'] == row['result'] == original['result']
        assert len(replay['frames']) == len(original['frames']) == row['plies'] + 1
        moves = []
        for i, (old, new) in enumerate(zip(original['frames'], replay['frames'])):
            assert old['ply'] == new['ply'] == i
            for key in ('ply', 'board', 'white', 'black', 'move'):
                assert old[key] == new[key], (game, i, key)
            if i:
                moves.append(new['move'])
            else:
                assert new['move'] is None
            clocks = new.get('clocks')
            assert isinstance(clocks, list) and len(clocks) == 2
            assert all(type(c) in (int, float) and math.isfinite(c) for c in clocks)
            counts['matched_frames'] += 1
            counts['new_clock_frames'] += int('clocks' not in old)
        assert hashlib.sha256(' '.join(moves).encode()).hexdigest() == row['moves_sha256']
        assert set(supplement[game]['metadata']) == fields
        assert supplement[game]['metadata'] == {key: replay.get(key) for key in fields} == receipt['metadata']
        assert supplement[game]['original_sha256'] == source['sha256']
        assert supplement[game]['moves_sha256'] == row['moves_sha256']
        stamp = replay['createdAt']
        assert re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)', stamp)
        dates.append(datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone(timezone.utc))
        names_match = {s: replay[s] == row[s] for s in ('white', 'black')}
        assert names_match == receipt['name_matches']
        actual_ours = any(replay[s] == 'IAmAVirus' for s in ('white', 'black'))
        counts['actual_iamavirus_games'] += int(actual_ours)
        counts['false_iamavirus_games'] += int(not actual_ours)
        counts['incorrect_selected_seat_names'] += int(replay[side] != original[side])
        counts['games_with_any_name_correction'] += int(not all(names_match.values()))
        counts['selected_seat_loss'] += int((row['result'] == '1-0' and side == 'black') or
                                           (row['result'] == '0-1' and side == 'white'))
        for color in ('white', 'black'):
            version = replay.get(color + 'Version')
            assert version is None or (type(version) is int and version >= 0)
            counts['recovered_played_versions'] += int(version is not None)
            counts['corrected_synthetic_player_ids'] += int(row[color + 'PlayerId'] != replay.get(color + 'PlayerId'))
        correction = dict(id=game, selected_side=side, original_selected_team=original[side],
                          actual_selected_team=replay[side], actual_white=replay['white'], actual_black=replay['black'],
                          createdAt=stamp, actual_iamavirus=actual_ours)
        corrections.append(correction)
        if not actual_ours and len(examples) < 4:
            examples.append(correction)
    report = dict(at=datetime.now(timezone.utc).isoformat(), processed=len(receipts), recovered=len(supplement),
                  all_164_recovered=len(supplement) == len(sources) == 164, counts=dict(counts),
                  earliest_date=min(dates).isoformat() if dates else None,
                  latest_date=max(dates).isoformat() if dates else None,
                  provenance_examples=examples,
                  hashes={str(p): digest(p) for p in (OUT / 'plan.json', OUT / 'result.json',
                                                      OUT / 'execution.json', STORE / 'receipts.jsonl',
                                                      STORE / 'supplement.json', corpus, Path(__file__),
                                                      ROOT / 'learning/ingest.py', ROOT / 'harness/corpus_download.py')},
                  scope='Independent saved-byte, identity and team-attribution audit. No rules rerun, raw mutation, new export or training. Dates are displayed at microsecond precision here; original nanosecond strings are retained in supplements.')
    with (STORE / 'attribution-corrections.json').open('x') as stream:
        json.dump(corrections, stream, indent=2)
        stream.write('\n')
    with (OUT / 'review.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ('processed', 'recovered', 'all_164_recovered', 'counts')}))


if __name__ == '__main__':
    main()
