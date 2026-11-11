"""Collect a fixed public replay window with the original clocks and views."""
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import math
from pathlib import Path
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
STORE = ROOT/'data/astra-spool'
PRIVATE = STORE/HERE.name
PROSPECTIVE = EXPERIMENTS/'prospective-quiet-teacher-20261110'
SEALED = STORE/PROSPECTIVE.name/'cohort.json'
PACKED = STORE/'recovered-replay-cache-20261110/games.json'
REFEREE = ROOT.parent/'fow-starter/referee.py'
VALIDATOR = EXPERIMENTS/'last-only-pilot-20261110/build/native-validator.so'
sys.path[:0] = [str(PROSPECTIVE),str(ROOT)]
from collect import BudgetClient, snapshot, source
from protocol import OWN, TEAMS, check_pins, now, sha, stamp_ns, write
from learning import _native, ingest

NORMAL = {'King capturable','Threefold repetition','50-move rule','No legal moves','Move limit reached'}
START = '2026-11-10T23:02:22Z'
END = '2026-11-11T00:09:32Z'


def read(path):
    return json.loads(Path(path).read_text())


def freeze():
    proof = ANALYSIS/PROSPECTIVE.name/'terminal-verification.json'
    recovery = ANALYSIS/'recovered-replay-cache-20261110/terminal-verification.json'
    assert sha(SEALED)==read(proof)['cohort_sha256']
    assert stamp_ns(START)>stamp_ns(read(proof)['sealed_at'])
    manifest = PACKED.parent/'manifest.json'
    assert sha(manifest)==read(recovery)['manifest_sha256']
    assert sha(PACKED)==read(manifest)['sha256']['games.json']
    assert stamp_ns(END)<stamp_ns(now())
    paths = [Path(__file__),PROSPECTIVE/'collect.py',PROSPECTIVE/'protocol.py',SEALED,PACKED,manifest,
             proof,recovery,REFEREE,VALIDATOR,ROOT/'learning/api_client.py',ROOT/'learning/ingest.py',
             ROOT/'learning/rules.py',ROOT/'learning/_native.py']
    plan = dict(at=now(),start=START,end=END,page_cap=12,request_cap=200,replay_limit=144,
                replay_bytes_cap=2*1024**2,total_bytes_cap=128*1024**2,wall_seconds=480,
                team_ids=sorted({*TEAMS,OWN}),
                selection='One fixed-cursor snapshot. Include own and reference games with normal outcomes. Own games first, then chronological. At most 144 replay reads; skip packed and prior sealed trajectory duplicates.',
                dependencies={str(path):sha(path) for path in paths})
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json',plan,exclusive=True)
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),pins=len(paths))),flush=True)


def validate(ref, row, replay):
    for field in ('id','createdAt','result','reason','white','black','whitePlayerId','blackPlayerId','whiteVersion','blackVersion'):
        assert replay.get(field)==row.get(field), (row['id'],field)
    assert replay['rulesVersion']=='fow-v1'
    frames = replay['frames']
    assert len(frames)==row['plies']+1
    board = ref.FowBoard()
    visits = Counter({ref.position_key(board):1})
    moves = []
    for ply,frame in enumerate(frames):
        clocks = frame['clocks']
        assert frame['ply']==ply and len(clocks)==2
        assert all(type(value) in (int,float) and math.isfinite(value) and value>=0 for value in clocks)
        if ply:
            text = frame['move']
            move = ref.chess.Move.from_uci(text)
            assert move in ref.fow_moves(board)
            board.push(move)
            visits[ref.position_key(board)]+=1
            moves.append(text)
        else:
            assert frame['move'] is None
        expected = ref.make_frame(board,frame['clocks'])
        assert all(expected[field]==frame[field] for field in ('board','white','black'))
        outcome = ref.outcome(board,visits)
        if ply<len(frames)-1:
            assert outcome is None
    if outcome is None and len(moves)==1000:
        outcome = ('1/2-1/2','Move limit reached')
    assert outcome is not None and tuple(outcome)==(row['result'],row['reason'])
    states, errors = ingest.validate_replay(replay)
    assert not errors and len(states)==len(frames),(row['id'],errors)
    assert states[-1].outcome()==outcome or len(moves)==1000 and row['reason']=='Move limit reached'
    return hashlib.sha256(' '.join(moves).encode()).hexdigest()


def run():
    plan = read(OUT/'plan.json')
    check_pins(plan)
    PRIVATE.mkdir(exist_ok=False)
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    spec = spec_from_file_location('later_window_course_ref',REFEREE)
    ref = module_from_spec(spec); spec.loader.exec_module(ref)
    client = BudgetClient(plan['request_cap'])
    status = dict(started_at=now(),plan_sha256=sha(OUT/'plan.json'),status='running')
    write(OUT/'execution.json',status,exclusive=True)
    def timeout(*_):
        raise TimeoutError('fixed replay window ingest exceeded its time bound')
    signal.signal(signal.SIGALRM,timeout)
    signal.alarm(plan['wall_seconds'])
    try:
        _, pages = snapshot(client,plan['start'],PRIVATE,0,plan['page_cap'])
        window = []
        lo,hi = stamp_ns(plan['start']),stamp_ns(plan['end'])
        for page in sorted(PRIVATE.glob('page-*.json')):
            window.extend(row for row in read(page)['page']['games'] if lo<=stamp_ns(row['createdAt'])<hi)
        allowed = set(plan['team_ids'])
        selected = [row for row in window if allowed.intersection((row['whitePlayerId'],row['blackPlayerId']))]
        priority = lambda row: OWN in (row['whitePlayerId'],row['blackPlayerId'])
        normal = sorted((row for row in selected if row['reason'] in NORMAL and row['plies']>=4),
                        key=lambda row: (not priority(row),stamp_ns(row['createdAt']),row['id']))
        denied = {row['sequence_sha256'] for row in read(PACKED)}
        denied.update(row['sequence_sha256'] for row in read(SEALED)['games'])
        frames = duplicates = 0
        size = sum(p.stat().st_size for p in PRIVATE.glob('page-*.json'))
        games = []
        own = Counter()
        for index,row in enumerate(normal[:plan['replay_limit']],1):
            replay,fetch = source(row,client,plan,PRIVATE)
            size += sum(p.stat().st_size for p in (PRIVATE/'games'/row['id']).iterdir())
            assert size<=plan['total_bytes_cap']
            digest = validate(ref,row,replay)
            if digest in denied:
                duplicates+=1
            else:
                denied.add(digest)
                games.append(dict(game=row['id'],sequence_sha256=digest,replay_sha256=fetch['sha256'],
                                  frames=len(replay['frames']),listing=row))
                frames += len(replay['frames'])
                if priority(row):
                    side = 'white' if row['whitePlayerId']==OWN else 'black'
                    own[str(row[side+'Version'])]+=1
            if index%24==0:
                print(json.dumps(dict(downloaded=index,eligible=len(games))),flush=True)
        assert games
        index = PRIVATE/'cohort.json'
        write(index,dict(plan_sha256=sha(OUT/'plan.json'),games=games),exclusive=True)
        size += index.stat().st_size
        assert size<=plan['total_bytes_cap']
        report = dict(at=now(),start=plan['start'],end=plan['end'],listed_games=len(window),reference_games=len(selected),
                      normal_reference_games=len(normal),downloaded=min(len(normal),plan['replay_limit']),games=len(games),frames=frames,
                      duplicate_trajectories=duplicates,other_terminations=dict(Counter(row['reason'] for row in selected if row['reason'] not in NORMAL)),
                      own_played_versions=dict(own),requests=client.requests_made,pages=pages,private_bytes=size,
                      source_pages={p.name:sha(p) for p in PRIVATE.glob('page-*.json')},cohort_sha256=sha(index),
                      plan_sha256=sha(OUT/'plan.json'),course_and_native_verified=True)
        write(OUT/'result.json',report,exclusive=True)
        status.update(status='complete',result_sha256=sha(OUT/'result.json'))
        print(json.dumps(report),flush=True)
    except BaseException as error:
        status.update(status='failed',error=repr(error))
        raise
    finally:
        signal.alarm(0)
        write(OUT/'execution.json',dict(**status,ended_at=now(),requests=client.requests_made))


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
