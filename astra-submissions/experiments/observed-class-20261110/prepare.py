"""Build/pin a native component check using old TRAIN data only; no scores."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/observed-class-20261110';BUILD=HERE/'build'
BASE=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/src'
RANK=HERE.parent/'observation-rank-20261110/rank.c'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    manifest=json.loads((ROOT/'astra-submissions/v38-manifest.json').read_text())
    for name,h in manifest['source_sha256'].items():
        if name.startswith('src/'):
            assert sha(BASE/Path(name).name)==h,name
    commands=[]
    common=['-std=c11','-pthread','-I'+str(BASE),str(HERE/'producer.c'),str(RANK),str(BASE/'board.c'),str(BASE/'movemodel.c'),'-lm']
    for cmd in [['gcc','-O2','-shared','-fPIC',*common,'-o',str(BUILD/'producer.so')],
                ['gcc','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DASTRA_CLASS_UNIT',*common,'-o',str(BUILD/'unit-sanitize')]]:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        commands.append(dict(argv=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (OUT/'build.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert r.returncode==0,r.stderr
    oldpath=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
    old=json.loads(oldpath.read_text())
    games=[dict(game=g['game'],moves=g['moves'][:40],original_sequence_sha256=g['sequence_sha256'])
           for g in old['games'] if g['split']=='train' and len(g['moves'])>=60][:16]
    assert len(games)==16
    fixtures=[
      dict(label='white-en-passant',fen='4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1',target='e5d6'),
      dict(label='black-en-passant',fen='4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1',target='e4d3'),
      dict(label='white-castle-through-attack',fen='4kr2/8/8/8/8/8/8/R3K2R w KQ - 0 1',target='e1g1'),
      dict(label='black-castle-through-attack',fen='r3k2r/8/8/8/8/8/8/4KR2 b kq - 0 1',target='e8g8'),
      dict(label='white-castle-into-attack-candidate',fen='4k1r1/8/8/8/8/8/8/R3K2R w KQ - 0 1',target='h1h2'),
      dict(label='king-must-escape',fen='4r2k/8/8/8/8/8/7P/4K3 w - - 0 1',target='e1d1'),
      dict(label='white-promotion-quiet',fen='1r5k/P7/8/8/8/8/8/7K w - - 0 1',target='a7a8q'),
      dict(label='white-promotion-capture',fen='1r5k/P7/8/8/8/8/8/7K w - - 0 1',target='a7b8n'),
      dict(label='black-promotion-quiet',fen='7k/8/8/8/8/8/7p/K5R1 b - - 0 1',target='h2h1q'),
      dict(label='black-promotion-capture',fen='7k/8/8/8/8/8/7p/K5R1 b - - 0 1',target='h2g1n'),
      dict(label='white-king-capture-candidate',fen='k7/Q7/8/8/8/8/8/7K w - - 0 1',target='h1h2'),
      dict(label='black-king-capture-candidate',fen='k7/8/8/8/8/8/7q/7K b - - 0 1',target='a8a7'),
      dict(label='empty-class-white-parent',fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
           view_fen='rnbqkbnr/pppppppp/8/5N2/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1',view_target='f5e7'),
      dict(label='empty-class-black-parent',fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1',
           view_fen='rnbqkb1r/pppppppp/8/8/5n2/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1',view_target='f4e2'),
    ]
    # Shape validation only; actual course/native parity is the frozen check.
    import sys
    sys.path.insert(0,str(ROOT.parent/'fow-starter'));import referee
    for f in fixtures:
        b=referee.FowBoard(f['fen'])
        if 'view_fen' in f:b=referee.FowBoard(f['view_fen'])
        m=referee.chess.Move.from_uci(f.get('target',f.get('view_target')))
        assert m in referee.fow_moves(b),f['label']
    deps=[HERE/'producer.c',HERE/'check.py',Path(__file__),RANK,oldpath,BUILD/'producer.so',BUILD/'unit-sanitize',
          ROOT/'astra-submissions/v38-manifest.json',ROOT.parent/'fow-starter/referee.py']+list(BASE.glob('*'))
    plan=dict(at=datetime.now(timezone.utc).isoformat(),games=games,fixtures=fixtures,
              selection='First16 existing293TRAIN games with>=60plies in frozen order; first40moves each. No outcome/model score selection.',
              source_parent='exact v38 native sources; default native king-pruning semantics',
              dependencies={str(p):sha(p) for p in sorted(set(deps))},
              max_seconds=120,scope='Native observed-class/mask and synthetic-weight correctness only. No learned ranking/model evaluation, future295data, filter/posterior/clock change or strength test.',
              acceptance='Every legal move/capture/view/native-king mask agrees with separate course rules; parent nonmutation; optional-view paths identical; masked values/capture events fixed;20nontrivial ambiguity/synthetic-reordering cases; all special-rule categories exercised.',
              limit='King capture/mover-king-pruning only. Hidden-history draws, actual filter cap/merge/history weighting and runtime costs are not certified.')
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(prepared=True,games=len(games),fixtures=len(fixtures),source_pins=len(plan['dependencies']))),flush=True)


if __name__=='__main__':main()
