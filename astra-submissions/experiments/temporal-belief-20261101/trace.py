#!/usr/bin/env python3
"""One isolated process per arm/game; views advance the model, truth only probes it."""
import argparse,ctypes as C,json,math,time
from pathlib import Path

def library(path):
    lib=C.CDLL(str(path.resolve()))
    lib.tb_create.argtypes=[C.c_int,C.c_size_t,C.c_uint64];lib.tb_create.restype=C.c_void_p
    lib.tb_free.argtypes=[C.c_void_p];lib.tb_free.restype=None
    lib.tb_step.argtypes=[C.c_void_p,C.c_char_p,C.c_char_p];lib.tb_step.restype=C.c_size_t
    lib.tb_checksum.argtypes=[C.c_void_p];lib.tb_checksum.restype=C.c_uint64
    lib.tb_probe.argtypes=[C.c_void_p,C.c_char_p,C.c_int,C.c_uint64,C.c_int,C.c_uint32,C.POINTER(C.c_double)]
    lib.tb_probe.restype=None
    lib.tb_king_risk.argtypes=[C.c_void_p,C.c_char_p];lib.tb_king_risk.restype=C.c_double
    return lib
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--truth',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--cap',type=int,default=20000);ap.add_argument('--seed',type=int,default=11012026)
    ap.add_argument('--redact-truth',action='store_true');ap.add_argument('--max-ply',type=int,default=80);args=ap.parse_args()
    feed=json.loads(args.input.read_text());truth={r['ply']:r for r in json.loads(args.truth.read_text())['rows']}
    lib=library(Path(__file__).resolve().parent/'build/libtemporal.so');h=lib.tb_create(feed['us'],args.cap,args.seed)
    if not h:raise MemoryError('native belief allocation')
    updates=[];decisions=[];total=0
    try:
        for step in feed['steps']:
            ply=step['ply']
            if ply>args.max_ply:break
            t=time.perf_counter()
            if ply:lib.tb_step(h,step['own_move'].encode() if step['own_move'] else None,step['view'].encode())
            dt=time.perf_counter()-t;total+=dt;checksum=lib.tb_checksum(h)
            updates.append({'ply':ply,'seconds':dt,'checksum':f'{checksum:016x}'})
            if 'next_own_move' not in step:continue
            label=truth[ply];out=(C.c_double*10)()
            lib.tb_probe(h,None if args.redact_truth else label['board'].encode(),label['side'],label['castle'],label['ep'],label['opponent_context'],out)
            risk=lib.tb_king_risk(h,step['next_own_move'].encode())
            assert lib.tb_checksum(h)==checksum,'diagnostics mutated the filter'
            row=dict(zip(['worlds','unique_boards','truth_share','truth_context_share','known_history_share','board_entropy','entry_ess','overflowed','truth_entries','truth_context_entries'],out))
            row.update(ply=ply,king_risk=risk if math.isfinite(risk) else None,actual_king_loss=label['fatal'],elapsed_updates=total)
            decisions.append(row)
    finally:lib.tb_free(h)
    result={'game':feed['id'],'us':feed['us'],'cap':args.cap,'seed':args.seed,'updates':updates,'decisions':decisions,'total_update_seconds':total,'truth_redacted':args.redact_truth}
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'game':feed['id'],'decisions':len(decisions),'update_seconds':total,'last_worlds':decisions[-1]['worlds'] if decisions else 0}))
if __name__=='__main__':main()
