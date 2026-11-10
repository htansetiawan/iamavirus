"""Exact material-ledger counterexamples; no policy execution or learned model."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/promotion-ledger-20261110'
NATIVE=ROOT/'astra-submissions/experiments/farsight-root-20261110/build/control/src'
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

VALUE={ref.chess.PAWN:1,ref.chess.KNIGHT:3,ref.chess.BISHOP:3,ref.chess.ROOK:5,ref.chess.QUEEN:9,ref.chess.KING:0}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def board_string(b):return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
def margin(b,us):return sum(VALUE[p.piece_type]*(1 if p.color==us else -1) for p in b.piece_map().values())
def lost(b):
    k=b.king(not b.turn)
    return k is None or b.is_attacked_by(b.turn,k)
def position(pieces,us):
    b=ref.FowBoard(None);b.turn=us
    for square,piece in pieces.items():
        if piece is not None:b.set_piece_at(ref.chess.parse_square(square),ref.chess.Piece.from_symbol(piece))
    return b


def reference(parent,uci,threshold=4):
    us=parent.turn;start=margin(parent,us);b=parent.copy();move=ref.chess.Move.from_uci(uci)
    assert move in ref.fow_moves(b);b.push(move);assert not lost(b)
    cases=[]
    for reply in ref.fow_moves(b):
        if b.piece_at(reply.to_square)!=ref.chess.Piece(ref.chess.QUEEN,us):continue
        q=b.copy();q.push(reply)
        if lost(q):continue
        best=margin(q,us);recaptures=[]
        for answer in ref.fow_moves(q):
            if answer.to_square!=reply.to_square:continue
            z=q.copy();z.push(answer)
            if not lost(z):
                best=max(best,margin(z,us));recaptures.append(answer.uci())
        cases.append(dict(reply=reply.uci(),material_before=start,material_after_root=margin(b,us),
                          best_material_after_capture_and_optional_recapture=best,net_loss=start-best,legal_safe_recaptures=recaptures))
    maximum=max((x['net_loss'] for x in cases),default=0)
    return dict(risk=int(maximum>=threshold),worst_net_loss=maximum,captures=cases)


def main():
    OUT.mkdir(exist_ok=False);build=HERE/'build';build.mkdir(exist_ok=False)
    # Verify that the proposed patch is exactly one promotion-credit addition.
    source=(NATIVE/'main.c').read_text();raw=gzip.decompress((HERE/'promotion-ledger.patch.gz').read_bytes())
    assert b'got += piece_pawns[promotion] - piece_pawns[PAWN];' in raw
    cmd=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(NATIVE),
         str(HERE/'bridge.c'),*[str(NATIVE/(n+'.c')) for n in ['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval']],'-lm','-o',str(build/'probe')]
    compiled=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    (OUT/'compile.stderr').write_text(compiled.stderr);assert compiled.returncode==0,compiled.stderr
    fixtures=[]
    def add(name,b,m):fixtures.append((name,b,m))
    black={'h8':'k','g1':'K','f1':'R','a2':'p'}
    white={'h8':'k','g1':'K','f8':'r','a7':'P'}
    for suffix in 'qrbn':
        add('black-quiet-promotion-'+suffix,position(black,False),'a2a1'+suffix)
        add('white-quiet-promotion-'+suffix,position(white,True),'a7a8'+suffix)
    add('black-capture-promotion',position({'h8':'k','g1':'K','f1':'R','a1':'R','b2':'p'},False),'b2a1q')
    add('white-capture-promotion',position({'h8':'k','g1':'K','f8':'r','a8':'r','b7':'P'},True),'b7a8q')
    add('ordinary-black-queen',position({**black,'a2':'q'},False),'a2a1')
    add('ordinary-white-queen',position({**white,'a7':'Q'},True),'a7a8')
    add('ordinary-queen-capture',position({'h8':'k','g1':'K','f1':'R','a1':'R','b2':'q'},False),'b2a1')
    path=ROOT/'data/astra-spool/v38-latest-ten-20261110/0xe4vmwz.json';rp=json.loads(path.read_text());real=ref.FowBoard()
    for f in rp['frames'][1:66]:real.push_uci(f['move'])
    for move in ['a2a1q','a2a1r','d4f2','d4c4']:add('recorded-prefix-'+move,real.copy(),move)
    # Corners: the opponent's capture also promotes, with and without recapture.
    both={'h8':'k','g1':'K','f8':'r','a7':'P','d1':'Q','e2':'p'}
    add('both-promotions-without-recapture',position(both,True),'a7a8q')
    add('both-promotions-with-recapture',position({**both,'g1':None,'c1':'K'},True),'a7a8q')
    enemy={'h8':'k','h1':'K','f8':'r','a8':'q','a1':'R','d1':'Q','e2':'p'}
    add('opponent-promotion-after-our-queen-capture',position(enemy,True),'a1a8')
    add('opponent-promotion-with-recapture',position({**enemy,'h1':None,'c1':'K'},True),'a1a8')
    # Save all intended function inputs and ledger expectations before invocation.
    expected=[dict(name=name,board=board_string(b),move=move,reference=reference(b,move)) for name,b,move in fixtures]
    write(OUT/'fixtures.json',dict(at=datetime.now(timezone.utc).isoformat(),threshold=4,cases=expected,
        scope='Synthetic correctness fixtures plus already selected pre-noon true position; no policy outcome selection.'))
    lines=[]
    for name,b,move in fixtures:
        lines.append(f"{board_string(b)} {0 if b.turn else 1} {b.castling_rights:x} {b.ep_square if b.ep_square is not None else -1} {move} 4")
    proc=subprocess.run([str(build/'probe')],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=20)
    (OUT/'probe.stdout').write_text(proc.stdout);(OUT/'probe.stderr').write_text(proc.stderr)
    assert proc.returncode==0,(proc.returncode,proc.stderr)
    native=[json.loads(line) for line in proc.stdout.splitlines()];assert len(native)==len(fixtures)
    results=[]
    for i,(item,n) in enumerate(zip(expected,native)):
        assert n['case']==i
        assert n['ledger']==[item['reference']['risk']]*2,(item,n)
        changed=n['old']!=n['ledger']
        results.append(dict(**item,**n,changed=changed))
    changed=[r['name'] for r in results if r['changed']]
    assert set(changed)=={'black-quiet-promotion-q','white-quiet-promotion-q','black-capture-promotion','white-capture-promotion','recorded-prefix-a2a1q','both-promotions-with-recapture','opponent-promotion-after-our-queen-capture'}
    partial_wrong=[r['name'] for r in results if r['root_credit']!=[r['reference']['risk']]*2]
    assert set(partial_wrong)=={'both-promotions-without-recapture','opponent-promotion-after-our-queen-capture'}
    ordinary=[r for r in results if r['name'].startswith('ordinary-')]
    assert all(r['old']==r['ledger']==[1.,1.] for r in ordinary)
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,cases=len(results),changed=changed,
        all_corrected_risks_match_exact_course_material_ledger=True,ordinary_queen_loss_controls_stay_positive=True,
        original_mismatches=sum(r['old']!=[r['reference']['risk']]*2 for r in results),root_credit_mismatches=partial_wrong,results=results,
        scope='Correctness of promotion material changes and recaptures for both sides on21fixed fixtures; no deployment, policy, playing strength or global guard-correctness claim.',
        limitations=['The original terminal-capture/recapture approximations remain unchanged.','Queen and rook promotion both permit the recorded Qg8 king net; crediting material does not save that game by itself.','No broader replay/match gate or arena version is earned by this check.'],
        source_hashes={str(p):sha(p) for p in [Path(__file__),HERE/'bridge.c',HERE/'promotion-ledger.patch.gz',NATIVE/'main.c',build/'probe',path,ROOT.parent/'fow-starter/referee.py']},compile_command=cmd)
    write(OUT/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['results','source_hashes','compile_command']},indent=2),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as error:
        if OUT.is_dir() and not (OUT/'failure.json').exists():
            write(OUT/'failure.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error)))
        raise
