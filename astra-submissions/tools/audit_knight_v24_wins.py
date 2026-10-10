"""Verify the two reported arena wins against the immutable v24 replay book."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import analyze_mist


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--referee', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location('course_referee', args.referee)
    referee = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referee)
    analyze_mist.TEAM = 'Knight Vision'
    with ZipFile(args.archive) as archive:
        book_bytes = archive.read('replay.txt')
    book = {}
    for line in book_bytes.decode().splitlines():
        color, view, moves, *_ = line.split('|')
        book.setdefault((color, view), moves.split(':')[0])
    result = {'archive': str(args.archive),
              'archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
              'book_sha256': hashlib.sha256(book_bytes).hexdigest(),
              'referee_sha256': hashlib.sha256(args.referee.read_bytes()).hexdigest(),
              'scope': 'Exact rules/board/observations/outcomes plus archived book lookup. Matching moves do not expose internal runtime branch telemetry. Two games do not prove universal determinism.',
              'games': []}
    args.output.mkdir(parents=True, exist_ok=True)
    for gid in ('da7pinqq', '12j9j4qe'):
        raw = (args.source / (gid + '.json')).read_bytes()
        replay = json.loads(raw)
        row = analyze_mist.analyze(replay, referee)
        ours = 'white' if replay['white'] == 'IAmAVirus' else 'black'
        assert replay[ours+'Version'] == 24 and row['version'] == 29
        matches, elapsed = [], []
        for before, after in zip(replay['frames'], replay['frames'][1:]):
            if ('white' if after['ply'] % 2 else 'black') != ours:
                continue
            expected = book.get((ours, before[ours]))
            matches.append({'ply': after['ply'], 'played': after['move'], 'book': expected,
                            'matches': expected == after['move']})
            side = 0 if ours == 'white' else 1
            elapsed.append(before['clocks'][side] + replay['timeControl']['incrementSeconds'] - after['clocks'][side])
        terminal = dict(row['terminal'])
        terminal['knight_vision_material_margin'] = terminal.pop('mist_material_margin')
        (args.output / (gid + '.json')).write_bytes(raw)
        result['games'].append({'id': gid, 'source': 'https://6s890.lids.mit.edu/api/games/'+gid,
            'replay_sha256': hashlib.sha256(raw).hexdigest(), 'createdAt': replay['createdAt'],
            'our_color': ours, 'our_version': 24, 'opponent_version': 29,
            'result': replay['result'], 'plies': row['plies'], 'validated_frames': len(replay['frames']),
            'book_moves': matches, 'all_our_moves_match_book': all(m['matches'] for m in matches),
            'total_our_clock_spend_seconds': sum(elapsed), 'max_our_move_seconds': max(elapsed),
            'terminal': terminal})
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'archive_sha256':result['archive_sha256'], 'games': [
        {'id':g['id'], 'plies':g['plies'], 'book_matches':sum(m['matches'] for m in g['book_moves']),
         'our_moves':len(g['book_moves']), 'safe_replies':g['terminal']['safe_alternatives']}
        for g in result['games']]}))


if __name__ == '__main__':
    main()
