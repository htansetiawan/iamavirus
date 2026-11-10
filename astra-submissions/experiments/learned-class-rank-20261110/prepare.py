"""Freeze an old-training-only necessary-signal check; never fit or select."""
from pathlib import Path
from datetime import datetime, timezone
import ctypes
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/learned-class-rank-20261110'
OLD = ROOT / 'astra-submissions/analysis/capture-fixed-prior-20261110'
COMPONENT = ROOT / 'astra-submissions/analysis/observed-class-20261110'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v):
    with p.open('x') as f: json.dump(v, f, indent=2, allow_nan=False); f.write('\n')


def main():
    OUT.mkdir(exist_ok=False)
    build = HERE / 'build'; build.mkdir(exist_ok=False)
    cmd = ['gcc', '-O3', '-std=c11', '-shared', '-fPIC', str(HERE/'native_math.c'), '-lm', '-o', str(build/'native_math.so')]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    lib = ctypes.CDLL(str(build/'native_math.so'))
    F=ctypes.c_float; U=ctypes.c_uint
    lib.astra_history_logp.argtypes=[ctypes.c_int,ctypes.POINTER(F),ctypes.POINTER(U),U,ctypes.POINTER(F)]
    cases=0
    for total in (0,1,2,3,4,127,65536):
        old=(F*3)(-1,-2,-3); counts=(U*3)(*([0,0,0] if total<3 else [total-2,1,1]));out=(F*3)()
        assert lib.astra_history_logp(3,old,counts,total,out)==0
        if total<3: assert bytes(old)==bytes(out)
        else:
            # Independent double expression only bounds rounding, not bit parity.
            import math
            for j in range(3):
                ref=math.log((int(counts[j])+4*math.exp(old[j]))/(total+4))
                assert abs(out[j]-ref)<2e-6
        cases+=1
    cplan=json.loads((COMPONENT/'plan.json').read_text())
    oldplan=json.loads((OLD/'plan.json').read_text())
    original={g['game']:g for g in oldplan['games'] if g['split']=='train'}
    games=[]
    for g in cplan['games']:
        o=original[g['game']]
        games.append(dict(**g,white=o['white'],black=o['black'],
                          selected_plies=[p for p in o['selected_plies'] if p<len(g['moves'])]))
    deps=dict(cplan['dependencies'])
    prior=ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110'
    deps.update({str(p):sha(p) for p in [
        COMPONENT/'plan.json',COMPONENT/'result.json',OLD/'plan.json',
        OLD/'22-linear-model.json',OLD/'22-quadratic-model.json',
        prior/'bridge.c',prior/'quiet.h',prior/'build/bridge.so',
        ROOT/'astra-submissions/experiments/deployed-prior-comparison-20261102/prior.c',
        ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/data/history.bin',
        HERE/'native_math.c',HERE/'run.py',HERE/'prepare.py',build/'native_math.so']})
    plan=dict(at=datetime.now(timezone.utc).isoformat(),games=games,teams=oldplan['teams'],
        dependencies=deps,cores=[0,1],max_seconds=120,
        primary='Exactly old293 TRAIN selected plies in the already fixed16 component traces, own move index>=8, reference mover, native surviving transition. Includes captures as unchanged controls.',
        models=['fixed22-quadratic primary','fixed22-linear comparator'],
        mechanism='Sort native post-history log likelihoods by fixed learned post-history scores only among same-parent received-view-consistent noncapturing survivors. Native full model only; no cheap change.',
        necessary_conditions=dict(primary_changed_min=20,primary_changed_games_min=4,primary_mean_tempered_log_gain_positive=True,
                                   primary_gain_vs_linear_positive=True,capture_and_mask_bits_exact=True,powered_class_multiset_exact=True),
        scope='Reused in-sample development feasibility, not confirmation, sequential posterior, runtime cost, match or strength. No parameters fitted or chosen. No295future source, prediction or result opened.',
        next='Failure closes these frozen scores for this mechanism on this development panel. A pass only earns a separate untouched-cohort design; no posterior/game/ZIP follows automatically.',
        nearest_prior=['228/229 observation decomposition already exists','231/232 posterior fits closed','293 combined configuration failed; selected full-only295 independent','299 mathematical permutation;300 native masks correct but only synthetic ranks'])
    write(OUT/'plan.json',plan)
    write(OUT/'preflight.json',dict(compile=cmd,native_history_synthetic_cases=cases,passed=True,
        learned_trace_scores_started=False,models_fitted=False,plan_sha256=sha(OUT/'plan.json')))
    print(json.dumps(dict(prepared=True,games=len(games),pinned=len(deps),plan_sha256=sha(OUT/'plan.json'))),flush=True)


if __name__=='__main__':main()
