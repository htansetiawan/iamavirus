"""Build the mass-preserving mode from the audited 343 engine inputs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = HERE.parent
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
STORE = ROOT/'data/astra-spool'/HERE.name
PREVIOUS = ROOT/'data/astra-spool/compact-prior-sequential-20261110'
NATIVE = ROOT/'data/astra-spool/compact-prior-native-20261110'
BASE = EXPERIMENTS/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
LEGACY = EXPERIMENTS/'quiet-prior-sequential-20261110'
sys.path.insert(0,str(LEGACY))
from run import environment, stable


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def replace(source, before, after):
    assert source.count(before)==1,before
    return source.replace(before,after)


def model_source(source):
    signature = '''void compact_full_logp(const Position *p, const MoveList *moves, Move previous,
                       int learned, float *out, float *residual) {'''
    source = replace(source,signature,'''static void compact_logp_pair(const Position *p, const MoveList *moves, Move previous,
                              int learned, float *out, float *residual, float *native) {''')
    end = '    if (quiet_count <= 1 || !changed) return;'
    source = replace(source,end,'''    if (native) memcpy(native, out, (size_t)moves->count * sizeof *out);
'''+end)
    return source+'''
void compact_full_logp(const Position *p, const MoveList *moves, Move previous,
                       int learned, float *out, float *residual) {
    compact_logp_pair(p, moves, previous, learned, out, residual, NULL);
}

void compact_likelihood_pair(const Position *p, const MoveList *moves, Move previous,
                             float *native, float *learned) {
    compact_logp_pair(p, moves, previous, 1, learned, NULL, native);
}
'''


def belief_source(source):
    source = replace(source,'static int use_compact_prior;','''static int use_compact_prior;
#include "redistribute.h"
void compact_likelihood_pair(const Position *, const MoveList *, Move, float *, float *);''')
    source = replace(source,'        if (strcmp(e, "2") == 0) use_compact_prior = 1;',
                     '''        if (strcmp(e, "3") == 0) use_compact_prior = 2;
        else if (strcmp(e, "2") == 0) use_compact_prior = 1;''')
    start = source.index('static void *opp_pass1(void *arg)')
    end = source.index('\n/* Moves the `keep`',start)
    worker = source[start:end]
    worker = replace(worker,'    float logit[256];','''    float logit[256];
    const int preserve = model_on && w->full && use_compact_prior == 2;''')
    worker = replace(worker,'''            if (w->full && use_compact_prior) {''',
                     '''            if (!preserve && w->full && use_compact_prior) {''')
    worker = replace(worker,'''            } else {
                move_logits(&p, &l, b->last_own, w->full, logit);''',
                     '''            } else if (!preserve) {
                move_logits(&p, &l, b->last_own, w->full, logit);''')
    worker = replace(worker,'''        const float base = b->logw ? b->logw[i] : 0.0f;''',
                     '''        const float base = b->logw ? b->logw[i] : 0.0f;
        const size_t first = w->n;
        int matched = 0, quiet_count = 0;
        uint16_t indices[256];
        uint8_t quiet[256];''')
    begin = worker.index('                    /* tempered log-likelihood')
    finish = worker.index('\n                }',begin)
    original = worker[begin:finish]
    worker = worker[:begin]+'''                    if (preserve) {
                        indices[matched] = (uint16_t)j;
                        quiet[matched] = u.captured_type == NO_PIECE;
                        quiet_count += quiet[matched++];
                    } else {
'''+ '\n'.join('    '+line for line in original.splitlines())+'''
                    }'''+worker[finish:]
    stop = '''            unmake_move(&p, l.moves[j], &u);
        }
    }'''
    worker = replace(worker,stop,'''            unmake_move(&p, l.moves[j], &u);
        }
        if (preserve && matched) {
            float compact[256], native_weight[256], compact_weight[256], adjusted[256];
            const Position *parent = &b->items[i];
            if (quiet_count > 1) compact_likelihood_pair(parent, &l, b->last_own, logit, compact);
            else compact_full_logp(parent, &l, b->last_own, 0, logit, NULL);
            for (int k = 0; k < matched; ++k) {
                const int j = indices[k];
                native_weight[k] = N > 0
                    ? model_temp * logf(((float)hc[j] + hist_n0 * expf(logit[j])) / ((float)N + hist_n0))
                    : model_temp * logit[j];
                compact_weight[k] = native_weight[k];
                if (quiet_count > 1 && quiet[k]) compact_weight[k] = N > 0
                    ? model_temp * logf(((float)hc[j] + hist_n0 * expf(compact[j])) / ((float)N + hist_n0))
                    : model_temp * compact[j];
            }
            preserve_quiet_mass(native_weight, compact_weight, quiet, matched, adjusted);
            for (int k = 0; k < matched; ++k) w->cand[first + k].logw = base + adjusted[k];
        }
    }''')
    return source[:start]+worker+source[end:]


def main():
    prior = read(PREVIOUS/'plan.json')
    verified = read(ANALYSIS/PREVIOUS.name/'terminal-verification.json')
    assert sha(PREVIOUS/'plan.json')==verified['plan_sha256']
    assert verified['failed_conditions']==['priority_nonregression']
    assert all(sha(path)==digest for path,digest in prior['dependencies'].items())
    OUT.mkdir(exist_ok=False); STORE.mkdir(exist_ok=False)
    (STORE/'movemodel.c').write_text(model_source((NATIVE/'movemodel.c').read_text()))
    (STORE/'belief.c').write_text(belief_source((PREVIOUS/'build/belief.c').read_text()))
    shutil.copyfile(NATIVE/'weights.h',STORE/'weights.h')
    flags = ['gcc','-O3','-std=c11','-pthread','-ffp-contract=off','-D_POSIX_C_SOURCE=199309L',
             '-I'+str(BASE/'src'),'-I'+str(LEGACY/'build'),'-I'+str(HERE)]
    command = flags+[str(LEGACY/'trace.c'),str(BASE/'src/board.c'),str(STORE/'belief.c'),
                     str(STORE/'movemodel.c'),'-lm','-o',str(STORE/'trace')]
    unit = flags+['-fsanitize=undefined','-fno-sanitize-recover=all',str(HERE/'unit.c'),'-lm','-o',str(STORE/'unit')]
    for cmd in (command,unit):
        subprocess.run(cmd,check=True,timeout=60)
    numeric = json.loads(subprocess.check_output([str(STORE/'unit')],text=True,timeout=20))
    preflight, changed = [], 0
    for side in (0,1):
        trace = PREVIOUS/f'fixture-{side}.trace'
        for seed in prior['seeds']:
            rows = {}
            for label,path,mode in (('original',PREVIOUS/'build/trace-original','0'),('zero',STORE/'trace','1'),
                    ('existing_learned',PREVIOUS/'build/trace-adapter','2'),('learned',STORE/'trace','2'),('preserved',STORE/'trace','3')):
                env = environment('original'); env['ASTRA_CAPTURE_FIXED'] = mode
                result = subprocess.run([str(path),str(trace),str(seed)],env=env,capture_output=True,text=True,check=True,timeout=20)
                rows[label] = [json.loads(line) for line in result.stdout.splitlines()]
                assert len(rows[label])==7 and all(row['matches'] and not row['guard_bad_moves'] for row in rows[label])
            assert stable(rows['original'])==stable(rows['zero'])
            assert stable(rows['existing_learned'])==stable(rows['learned'])
            changed += sum(a['signature']!=b['signature'] for a,b in zip(rows['original'],rows['preserved']))
            preflight.append(dict(side=side,calls=len(rows),rows=sum(map(len,rows.values()))))
    assert changed>0
    pins = [Path(__file__),HERE/'redistribute.h',HERE/'unit.c',PREVIOUS/'plan.json',
            ANALYSIS/PREVIOUS.name/'terminal-verification.json',*STORE.iterdir(),
            LEGACY/'trace.c',LEGACY/'run.py',LEGACY/'build/guard_predicates.h',BASE/'src/board.c',
            BASE/'src/fow.h',PREVIOUS/'build/trace-adapter',PREVIOUS/'build/trace-original',
            PREVIOUS/'fixture-0.trace',PREVIOUS/'fixture-1.trace',BASE/'data/history.bin']
    report = dict(at=now(),numeric=numeric,preflight_calls=sum(row['calls'] for row in preflight),
                  preflight_rows=sum(row['rows'] for row in preflight),preserved_signature_changes=changed,
                  binary_sha256=sha(STORE/'trace'),dependencies={str(p):sha(p) for p in pins},
                  scope='Standalone replay diagnostic. Original and unconstrained compact control parity. No deployment or playing decision.')
    save(OUT/'build.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='dependencies'},indent=2),flush=True)


if __name__=='__main__':
    main()
