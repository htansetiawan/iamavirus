"""Trace the first pilot's rebuild game under an equal fixed belief schedule."""
from datetime import datetime, timezone
import ctypes as C
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis'/HERE.name
BUILD = HERE/'build'
LEGACY = HERE.parent/'quiet-prior-sequential-20261110'
PRIVATE = ROOT/'data/astra-spool'/HERE.name/'rebuild-replay'
sys.path.insert(0,str(LEGACY))
from prepare import MoveList, NB, inspect_game, load_ref
from run import environment, stable


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    plan = read(OUT/'plan.json')
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    verified = read(OUT/'first-four-verification.json')
    assert verified['plan_sha256']==sha(OUT/'plan.json')
    # Select from the fixed first checkpoint by its native rebuild marker.
    games = []
    for receipt in verified['games']:
        path = Path(plan['store'])/'jobs'/receipt['game']/'replay.json'
        assert sha(path)==receipt['replay_sha256']
        replay = read(path)
        side = receipt['candidate_color']
        n = replay['privateDiagnostics'][side].count('mist: belief empty, rebuilt ')
        if n:
            games.append((receipt,replay,n))
    assert len(games)==1
    receipt,replay,rebuilds = games[0]
    observer = int(receipt['candidate_color']=='black')
    frontend = C.CDLL(str(NB/'adapter.so')); frontend.fow_init()
    frontend.view_moves.argtypes = [C.c_char_p,C.c_int,C.c_uint64,C.POINTER(MoveList)]
    # The historical C trace header uses a 15-byte ID field. Keep the real
    # pilot ID in the receipt and use a short label only in the adapter.
    trace_id = 'rebuild0'
    lines,unsupported,frames = inspect_game(load_ref(),frontend,dict(replay,id=trace_id),observer)
    assert not unsupported
    PRIVATE.mkdir(exist_ok=False)
    trace = PRIVATE/'observed.trace'
    trace.write_text('\n'.join(lines)+'\n')
    source = LEGACY/'trace.c'
    guard = LEGACY/'build/guard_predicates.h'
    old = ROOT/'data/astra-spool/compact-prior-sequential-20261110/plan.json'
    for path in (source,guard):
        assert sha(path)==read(old)['dependencies'][str(path)]
    refs = {}
    seed = read(old)['seeds'][0]
    for arm,folder in (('v38',BUILD/'base'),('deferred',BUILD/'candidate')):
        src = folder/'src'
        cmd = ['gcc','-O2','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I'+str(src),
               '-I'+str(guard.parent),str(source),*[str(src/name) for name in ('board.c','belief.c','movemodel.c')],
               '-lm','-o',str(PRIVATE/arm)]
        subprocess.run(cmd,check=True,timeout=60)
        env = environment('original'); env['MIST_THREADS'] = '1'
        result = subprocess.run([str(PRIVATE/arm),str(trace),str(seed)],env=env,capture_output=True,text=True,
                                timeout=120)
        (PRIVATE/(arm+'.stderr')).write_text(result.stderr)
        result.check_returncode()
        (PRIVATE/(arm+'.stdout')).write_text(result.stdout)
        refs[arm] = [json.loads(line) for line in result.stdout.splitlines()]
        assert len(refs[arm])==len(lines)-1
    assert stable(refs['v38'])==stable(refs['deferred'])
    native = refs['v38']
    first = lambda predicate:next((r['ply'] for r in native if predicate(r)),None)
    report = dict(at=datetime.now(timezone.utc).isoformat(),game=receipt['game'],source_replay_sha256=receipt['replay_sha256'],
                  played_rebuilds=rebuilds,course_frames=frames,matched_update_rows=len(native),
                  first_cap=first(lambda r:r['ever_capped']),first_truth_absence=first(lambda r:not r['matches']),
                  first_empty_population=first(lambda r:not r['worlds']),
                  trace_hash=sha(trace),trace_id=trace_id,native_source_sha256=sha(source),
                  arm_sha256={key:sha(PRIVATE/key) for key in refs},
                  scope='One selected local pilot game, fixed 200k cap, one updater thread, no clock thinning or rebuild. The score and playing gate are untouched. This comparison tests native equivalence on the same path and does not reconstruct the exact played belief.')
    with (OUT/'first-rebuild-replay.json').open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
