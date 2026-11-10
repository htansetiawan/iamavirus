"""Resource-priority census and deterministic guard masks, never a playing gate."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/promotion-reach-20261110'
BUILD=HERE/'build'
TRAIN=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
POP=ROOT/'data/astra-spool/farsight-root-20261110/actor/population.json'
NATIVE=ROOT/'astra-submissions/experiments/farsight-root-20261110/build/control/src'
LEDGER=ROOT/'astra-submissions/experiments/promotion-ledger-20261110/bridge.c'
sys.path[:0]=[str(ROOT),str(ROOT.parent/'fow-starter')]
import referee as ref
from learning import rules


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def text(b):return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
def loses(b):
    king=b.king(not b.turn)
    return king is None or b.is_attacked_by(b.turn,king)


def prepare():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False)
    s=LEDGER.read_text();first=s.index('static void ledger_queen_risks(');last=s.rindex('\nint main(void)')
    (BUILD/'ledger.h').write_text(s[first:last])
    cmd=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(NATIVE),'-I',str(BUILD),
         str(HERE/'mask.c'),*[str(NATIVE/(n+'.c')) for n in ['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval']],'-lm','-o',str(BUILD/'mask')]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);(OUT/'compile.stderr').write_text(p.stderr)
    assert p.returncode==0,p.stderr
    games=[g for g in read(TRAIN)['games'] if g['split']=='train' and any(g[s].casefold()=='iamavirus' for s in ('white','black'))]
    assert len(games)==302 and len({g['game'] for g in games})==302
    deps=[Path(__file__),HERE/'mask.c',BUILD/'ledger.h',BUILD/'mask',TRAIN,POP,LEDGER,
          ROOT/'astra-submissions/analysis/farsight-root-20261110/audit.json',ROOT/'astra-submissions/analysis/promotion-ledger-20261110/result.json',
          ROOT/'learning/rules.py',ROOT/'learning/_native.py',ROOT/'build/librules.so',ROOT.parent/'fow-starter/referee.py']
    deps += [p for p in NATIVE.iterdir() if p.is_file()]
    write(OUT/'plan.json',dict(at=now(),games=[g['game'] for g in games],split='train',dependencies={str(p):sha(p) for p in deps},
        core_pair=[2,3],wall_seconds=180,mask_seconds=30,compile_command=cmd,
        scope='Descriptive opportunity census on all302 old own TRAIN games and fixed2128-world guard arithmetic at the already diagnosed Farsight root. No policy, new root reconstruction, model, threshold choice, validation/test/future data, match or promotion.',
        census='Every actual own decision before the recorded next move. Legal own promotions; safe own promotions; any opponent pawn on its penultimate rank and any king-safe root move permitting a pseudo-legal promoting capture of our queen. Compare every recorded transition/board with independent native rules. Own executed promotions counted separately.',
        limitations='Realized true histories are an oracle opportunity proxy, not the runtime hypothetical belief distribution, a strict bound on fix incidence or an Elo estimate. Selected fixed-belief mask is development evidence only.',
        nearest_prior='304 already scans these302 TRAIN games for a different bare-king opportunity;310 supplies correctness only. This measures promotion opportunity and fixed masks without reopening221/280/285 negative playing gates.',
        next='A mask difference is not a playing gate. Report small reach honestly; no automatic broader native prefix collection or games.'))
    print(json.dumps(dict(prepared=True,games=len(games),pins=len(deps))),flush=True)


def mask_result():
    pop=read(POP);lines=[f"{pop['count']} {pop['us']}"]
    for w in pop['worlds']:
        lines.append(f"{w['board']} {w['side']} {w['castle']} {w['ep']} {w['halfmove']} {w['logw']:.9g}")
    (OUT/'mask-input.txt').write_text('\n'.join(lines)+'\n')
    p=subprocess.run([str(BUILD/'mask')],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=30)
    (OUT/'mask.stdout').write_text(p.stdout);(OUT/'mask.stderr').write_text(p.stderr);assert p.returncode==0,p.stderr
    rows=[json.loads(s) for s in p.stdout.splitlines()];assert len(rows)==36
    masks={}
    for key in ['old_queen','ledger_queen']:
        combined={r['move']:[k+.9*q for k,q in zip(r['king'],r[key])] for r in rows}
        least=[min(v[i] for v in combined.values()) for i in range(2)]
        out={m for m,v in combined.items() if v[1]>least[1]+.02 or v[0]>least[0]+.02}
        if len(out)==len(rows):out={m for m,v in combined.items() if v[1]>least[1]+.02}
        masks[key]=sorted(out)
    original=read(ROOT/'astra-submissions/analysis/farsight-root-20261110/audit.json')['avoid_moves']
    assert set(original)==set(masks['old_queen'])
    return dict(rows=rows,masks=masks,newly_allowed=sorted(set(masks['old_queen'])-set(masks['ledger_queen'])),newly_excluded=sorted(set(masks['ledger_queen'])-set(masks['old_queen'])),original_native_mask_reproduced=True)


def run():
    plan=read(OUT/'plan.json')
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    leases=read(ROOT/'chatroom/cores.json')['allocation']
    assert any(x.get('lease')=='311-promotion-reach' and x.get('cores')==plan['core_pair'] for x in leases)
    assert not any(set(x.get('cores',[]))&set(plan['core_pair']) for x in leases if x.get('lease')!='311-promotion-reach')
    os.sched_setaffinity(0,set(plan['core_pair']))
    start=time.monotonic();games={g['game']:g for g in read(TRAIN)['games']};records=[];frames=0;decisions=0
    for game_id in plan['games']:
        assert time.monotonic()-start<150
        g=games[game_id];assert hashlib.sha256(' '.join(g['moves']).encode()).hexdigest()==g['sequence_sha256']
        us=g['white'].casefold()=='iamavirus';side=0 if us else 1
        b=ref.FowBoard();native=rules.Board();count=dict(game=game_id,side=side,version=g[('white_version','black_version')[side]],decisions=0,promotion_roots=[],opponent_promotion_capture_roots=[],played_promotions=[])
        assert text(b)==native.board_string();frames+=1
        for ply,uci in enumerate(g['moves']):
            if b.turn==us:
                decisions+=1;count['decisions']+=1
                own_mask=ref.chess.BB_RANK_7 if us else ref.chess.BB_RANK_2
                enemy_mask=ref.chess.BB_RANK_2 if us else ref.chess.BB_RANK_7
                own=b.pawns & b.occupied_co[us] & own_mask
                enemy=b.pawns & b.occupied_co[not us] & enemy_mask
                if own or enemy:
                    legal=ref.fow_moves(b);assert {m.uci() for m in legal}==set(native.legal_moves())
                    promotions=[m for m in legal if m.promotion]
                    if promotions:
                        safe=[]
                        for m in promotions:
                            q=b.copy();q.push(m)
                            if not loses(q) and q.king(not us) is not None:safe.append(m.uci())
                        count['promotion_roots'].append(dict(ply=ply,legal=[m.uci() for m in promotions],king_safe=safe))
                    if enemy:
                        paths=[]
                        for move in legal:
                            q=b.copy();q.push(move)
                            if loses(q) or q.king(not us) is None:continue
                            for reply in ref.fow_moves(q):
                                if reply.promotion and q.piece_at(reply.to_square)==ref.chess.Piece(ref.chess.QUEEN,us):
                                    z=q.copy();z.push(reply)
                                    paths.append(dict(root=move.uci(),reply=reply.uci(),reply_self_fatal=loses(z)))
                        if paths:count['opponent_promotion_capture_roots'].append(dict(ply=ply,paths=paths))
                if len(uci)==5:count['played_promotions'].append(dict(ply=ply,move=uci))
            move=ref.chess.Move.from_uci(uci);assert move in ref.fow_moves(b);b.push(move);native.push(uci)
            assert text(b)==native.board_string();frames+=1
        records.append(count)
    masks=mask_result()
    result=dict(at=now(),games=len(records),decisions=decisions,frames_verified=frames,
        games_with_legal_root_promotion=sum(bool(g['promotion_roots']) for g in records),
        legal_promotion_roots=sum(len(g['promotion_roots']) for g in records),
        games_with_king_safe_promotion=sum(any(r['king_safe'] for r in g['promotion_roots']) for g in records),
        king_safe_promotion_roots=sum(bool(r['king_safe']) for g in records for r in g['promotion_roots']),
        games_with_opponent_promotion_capture_context=sum(bool(g['opponent_promotion_capture_roots']) for g in records),
        opponent_promotion_capture_roots=sum(len(g['opponent_promotion_capture_roots']) for g in records),
        games_with_played_own_promotion=sum(bool(g['played_promotions']) for g in records),
        played_own_promotions=sum(len(g['played_promotions']) for g in records),
        fixed_belief_masks=masks,records=records,seconds=time.monotonic()-start,scope=plan['scope'],limitations=plan['limitations'])
    assert result['frames_verified']==27135
    write(OUT/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['records','fixed_belief_masks']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);action=parser.parse_args().action
    try:globals()[action]()
    except BaseException as e:
        if OUT.is_dir() and not(OUT/'failure.json').exists():write(OUT/'failure.json',dict(at=now(),action=action,error=repr(e)))
        raise
