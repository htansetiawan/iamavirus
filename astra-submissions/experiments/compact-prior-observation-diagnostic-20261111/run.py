"""Separate observed-view prediction from hidden move selection at the true parent."""
from collections import defaultdict
import ctypes as C
from importlib.util import module_from_spec, spec_from_file_location
import json
import math
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
SEQUENTIAL = ANALYSIS/'compact-prior-sequential-20261110'
RAW = ROOT/'data/astra-spool'/SEQUENTIAL.name
HOLDOUT = ANALYSIS/'compact-prior-holdout-20261110'
spec = spec_from_file_location('compact_oracle',HERE.parent/HOLDOUT.name/'run.py')
holdout = module_from_spec(spec); spec.loader.exec_module(holdout)
read, sha, write = holdout.read, holdout.sha, holdout.write


class Classes:
    def __init__(self, producer):
        nd = lambda dtype: np.ctypeslib.ndpointer(dtype=dtype,flags='C_CONTIGUOUS')
        self.query = producer.native.lib.astra_test_class
        self.query.argtypes = [C.c_int,C.c_char_p,nd(np.uint16),nd(np.uint8),nd(np.uint8),nd(np.uint8),C.c_void_p]
        self.moves = np.zeros(256,np.uint16)
        self.capture = np.zeros(256,np.uint8)
        self.matches = np.zeros(256,np.uint8)
        self.quiet = np.zeros(256,np.uint8)

    def mask(self, side, received, inputs, target):
        n = self.query(side^1,received.encode(),self.moves,self.capture,self.matches,self.quiet,None)
        assert n==len(inputs['native_moves']) and np.array_equal(self.moves[:n],inputs['native_moves'])
        assert np.array_equal(self.capture[:n]>0,inputs['x'][:,0]>0)
        take = self.matches[:n]>0
        assert take[target] and np.array_equal(self.quiet[:n]>0,take & (self.capture[:n]==0))
        return take


@torch.no_grad()
def rows_for_game(producer, classes, model, row):
    replay = read(row['raw_path'])
    observer = ('white','black')[row['observer']]
    frames = replay['frames']
    assert replay['id']==row['game'] and len(frames)==row['frames']
    game = dict(game=row['game'], frames=len(frames), moves=[f['move'] for f in frames[1:]],
                white=replay['white'],black=replay['black'])
    selected = [ply for ply in range(15,len(frames)-2) if ply%2 != row['observer']]
    game['selected_plies'] = selected
    inputs, masks, targets = [], [], []
    for example, meta in producer.game(game,replay):
        assert not meta['self_capturable']
        take = classes.mask(meta['ply']%2,frames[meta['ply']+1][observer],example,meta['target'])
        inputs.append(example); masks.append(take); targets.append(meta['target'])
    if not inputs:
        return []
    b = holdout.batch(inputs)
    scores = [holdout.quiet_logp(b['base'], delta, b['valid'], b['capture'],b['counts'],b['history_n']).numpy()
              for delta in (torch.zeros_like(b['base']),model(b))]
    result = []
    for i,(take,target) in enumerate(zip(masks,targets)):
        n = len(take)
        baseline, learned = (s[i,:n].astype(float) for s in scores)
        all_mass = [np.logaddexp.reduce(s) for s in (baseline,learned)]
        assert abs(all_mass[0]-all_mass[1])<4e-6
        observed = [np.logaddexp.reduce(s[take]) for s in (baseline,learned)]
        full = (learned[target]-all_mass[1])-(baseline[target]-all_mass[0])
        view = (observed[1]-all_mass[1])-(observed[0]-all_mass[0])
        within = (learned[target]-observed[1])-(baseline[target]-observed[0])
        assert abs(full-view-within)<1e-12
        result.append((full,view,within,int(take.sum())))
    assert len(result)==len(selected)
    return result


def summarize(groups):
    games = [values for values in groups if values]
    rows = [r for group in games for r in group]
    sums = np.array([np.array(group)[:,:3].sum(0) for group in games])
    sizes = np.array(list(map(len,games)))
    selected = np.random.default_rng(3522111).integers(len(games),size=(4000,len(games)))
    intervals = np.quantile(sums[selected].sum(1)/sizes[selected].sum(1)[:,None],[.025,.975],axis=0)
    mean = [math.fsum(row[i] for row in rows)/len(rows) for i in range(3)]
    return dict(games=len(games),decisions=len(rows),ambiguous=sum(row[3]>1 for row in rows),
                gain=dict(zip(('actual_move','received_view','within_view'),mean)),
                descriptive_intervals95={name:intervals[:,i].tolist()
                                         for i,name in enumerate(('actual_move','received_view','within_view'))})


def main():
    receipt = read(SEQUENTIAL/'terminal-verification.json')
    assert receipt['result_sha256']==sha(SEQUENTIAL/'result.json') and receipt['plan_sha256']==sha(RAW/'plan.json')
    earlier = read(RAW/'plan.json')
    plan = read(HOLDOUT/'plan.json')
    assert all(sha(path)==digest for path,digest in plan['dependencies'].items())
    torch.set_num_threads(1)
    producer = holdout.Producer(plan['native_state_library'])
    classes = Classes(producer)
    hard = holdout.load_models(plan)['hard']
    groups = defaultdict(list)
    for game in earlier['games']:
        assert sha(game['raw_path'])==earlier['dependencies'][game['raw_path']]
        groups[game['team']].append(rows_for_game(producer,classes,hard,game))
    report = dict(at=holdout.now(), source_result_sha256=receipt['result_sha256'], hard_checkpoint_sha256=sha(plan['weights']['hard']),
                  all=summarize([group for values in groups.values() for group in values]),
                  by_team={name:summarize(values) for name,values in groups.items()},
                  scope='True-parent, untempered, full-regime scores on the already scored development cohort. Neither head sees the received view. The view is used by the diagnostic to group legal moves after both heads are evaluated. No posterior, prospective, threshold selection or strength inference.')
    OUT.mkdir(exist_ok=False)
    write(OUT/'result.json',report,exclusive=True)
    print(json.dumps(dict(all=report['all'],instructors=report['by_team']['Instructors']),indent=2),flush=True)


if __name__=='__main__':
    main()
