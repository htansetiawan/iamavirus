"""One constructed composite-guard check; not an engine policy or strength test."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-integration-20261111"
TREE = HERE / "build/corrected/tree"


def main():
    prior = json.loads((OUT / "result.json").read_text())
    assert hashlib.sha256((TREE / "src/main.c").read_bytes()).hexdigest() == prior["amended_main_sha256"]
    original = (ROOT.parent / "fowsearch-c/src/main.c").read_text()
    assert hashlib.sha256(original.encode()).hexdigest() == prior["original_main_sha256"]
    default = 'getenv("MIST_PIECE_GUARD") ? atof(getenv("MIST_PIECE_GUARD")) : 0.758'
    assert default in original
    a = original.index("static void queen_risks("); b = original.index("\n/* Piece guard", a)
    original_queen = original[a:b].replace("static void queen_risks(", "static void astra_original_queen_risks(", 1)
    source = r'''
#define main astra_unused_protocol_main
#include "main.c"
#undef main
__ORIGINAL__
int main(void) {
 fow_init();zobrist_init(); char text[65];int id=0;
 while(scanf("%64s",text)==1){
  Position p;if(pos_from_board_string(&p,text,WHITE,0,-1)<0)return 2;
  Belief b={0};b.items=&p;b.count=1;b.us=WHITE;
  Move m=MAKE_MOVE(16,19,NO_PIECE);double old,ot,ou,q,qt,qu,r,rt,ru;
  astra_original_queen_risks(&b,m,1,2,4,&old,&ot,&ou);
  queen_risks(&b,m,1,2,4,&q,&qt,&qu);
  piece_risks(&b,m,1,2,3,4,&r,&rt,&ru);
  printf("{\"case\":%d,\"queen_original\":%.17g,\"queen_amended\":%.17g,\"piece_unchanged\":%.17g,\"combined\":%.17g}\n",id++,old,q,r,0.9*q+0.758*r);
 }
 return 0;
}
'''.replace("__ORIGINAL__", original_queen)
    (TREE / "src/partition-probe.c").write_text(source)
    oracle_path = ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py"
    spec = importlib.util.spec_from_file_location("existing_course_partition_reference", oracle_path)
    oracle = importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    chess,ref = oracle.ref.chess,oracle.ref
    boards = []
    pieces = {"e1":"K","e2":"B","a1":"R","a3":"Q","d3":"p","d8":"q","e8":"r","a8":"r","h8":"k"}
    for name,p in (("pinned-defender",pieces),("rook-removed-control",{k:v for k,v in pieces.items() if k!="e8"})):
        board=oracle.position(p,True);reference=oracle.reference(board,"a3d3")
        post=board.copy();post.push_uci("a3d3")
        capture=chess.Move.from_uci("a8a1");assert capture in ref.fow_moves(post)
        post.push(capture);assert not oracle.lost(post)
        answers=[]
        for answer in ref.fow_moves(post):
            if answer.to_square!=chess.A1:continue
            z=post.copy();z.push(answer)
            if not oracle.lost(z):answers.append(answer.uci())
        assert not answers and oracle.margin(board,True)-oracle.margin(post,True)==4
        boards.append(dict(name=name,board=oracle.board_string(board),queen_reference=reference,
                           other_piece_capture="a8a1",other_piece_net_loss=4,safe_recaptures=answers))
    inputs="\n".join(b["board"] for b in boards)+"\n"
    (OUT/"partition-cases.json").write_text(json.dumps(boards,indent=2)+"\n")
    sources=["board","belief","movemodel","cfr","eval","search","gtcfr","front","sfeval","partition-probe"]
    argv=["gcc","-std=c11","-O2","-pthread","-D_POSIX_C_SOURCE=199309L",*["src/"+n+".c" for n in sources],"-lm","-o","partition-probe"]
    compile_result=subprocess.run(argv,cwd=TREE,capture_output=True,text=True,timeout=15)
    assert compile_result.returncode==0,compile_result.stderr
    run=subprocess.run([str(TREE/"partition-probe")],input=inputs,capture_output=True,text=True,timeout=10)
    assert run.returncode==0,run.stderr
    rows=[json.loads(line) for line in run.stdout.splitlines()]
    assert len(rows)==2 and rows[0]["queen_amended"]==boards[0]["queen_reference"]["risk"]==1
    assert rows[1]["queen_amended"]==boards[1]["queen_reference"]["risk"]==0
    assert all(r["piece_unchanged"]==1 for r in rows)
    result=dict(diagnostic_completed=True,queen_only_patch_preserves_composite_partition=False,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,
                compile=dict(argv=argv,exit_code=compile_result.returncode,stderr=compile_result.stderr),
                probe_exit_code=run.returncode,policy_or_backend_runs=0,
                conclusion="Do not integrate the queen-only patch into current default composite guard. Its queen exclusion in best_capture_net needs the same safe-recapture semantics.",
                limits="Two constructed component positions; no population frequency, policy, performance or strength evidence. The 26 queen-helper compiler checks remain passing and narrow.")
    with (OUT/"partition-result.json").open("x") as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result))


if __name__=="__main__":main()
