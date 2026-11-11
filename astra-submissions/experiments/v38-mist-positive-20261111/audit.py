"""Curate both newly completed v38 wins over Mist with exact-rule labels."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis'/HERE.name
RAW = ROOT/'data/astra-spool/v38-mist-wins-20261111'
SNAPSHOT = ROOT/'astra-submissions/analysis/v38-leaderboard-20261111T0118Z'
REFEREE = ROOT.parent/'fow-starter/referee.py'
VALIDATOR = HERE.parent/'last-only-pilot-20261110/build/native-validator.so'

sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from audit_top6_tactics import audit, load_referee
from learning import _native, ingest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    listing = json.loads((SNAPSHOT/'games.json').read_text())['games']
    games = [game for game in listing if 'Mist Opportunities' in (game['white'], game['black'])]
    assert len(games) == 2
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    referee = load_referee(REFEREE)
    records = []
    frames = 0
    for game in games:
        source = RAW/(game['id']+'.json')
        replay = json.loads(source.read_text())
        for key in ('id', 'createdAt', 'white', 'black', 'whiteVersion', 'blackVersion', 'reason', 'result'):
            assert game[key] == replay[key]
        own = 'white' if game['white'] == 'IAmAVirus' else 'black'
        other = 'black' if own == 'white' else 'white'
        assert game[own+'Version'] == 38 and game[other+'Version'] == 2
        assert game['result'] == ('1-0' if own == 'white' else '0-1')
        states, errors = ingest.validate_replay(replay)
        assert not errors and len(states) == len(replay['frames'])
        assert states[-1].outcome() == (replay['result'], replay['reason'])
        loser = audit(replay, 'Mist Opportunities', referee)
        winner = audit(replay, 'IAmAVirus', referee)
        assert loser['score'] == 0 and winner['score'] == 1 and loser['terminal']
        frames += len(states)
        terminal = loser['terminal']
        records.append(dict(id=game['id'], our_color=own, completed_at=game['createdAt'],
            frames=len(states), replay_sha256=sha(source), ending=terminal,
            our_material_at_end=-terminal['material_margin'],
            tail=[frame['move'] for frame in replay['frames'][-7:]],
            source='https://6s890.lids.mit.edu/api/games/'+game['id']))
    dependencies = [Path(__file__), REFEREE, VALIDATOR, SNAPSHOT/'games.json',
                    ROOT/'astra-submissions/tools/audit_top6_tactics.py',
                    ROOT/'astra-submissions/tools/analyze_mist.py',
                    ROOT/'astra-submissions/tools/mine_top6_exploits.py',
                    ROOT/'learning/ingest.py', ROOT/'learning/rules.py', ROOT/'learning/_native.py']
    result = dict(at=datetime.now(timezone.utc).isoformat(), games=len(games), verified_frames=frames,
        current_archive='ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f',
        records=records, dependencies={str(path):sha(path) for path in dependencies},
        scope='All two newest recorded v38 games against Mist v2 in the frozen ten-game snapshot. Positive-pattern curation with C++ and course checks. Oracle terminal alternatives and hidden-attacker labels are diagnostics. No runtime policy change or match-rate inference.')
    OUT.mkdir(exist_ok=False)
    with (OUT/'result.json').open('x') as stream:
        stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    main()
