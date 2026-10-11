#!/usr/bin/env python3
"""Label all legal setup moves in exact singleton opening states, by structure."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from m4_information_dilemma import analyze


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cap-run',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--kit',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(exist_ok=False)
    sys.path.insert(0,str(args.kit));import referee,chess
    states={};sources={};eligible=0
    for batch in ['sequential02','sequential-fresh26']:
        source=args.cap_run/batch/'mode0.jsonl';sources[str(source)]=sha(source)
        for r in map(json.loads,source.read_text().splitlines()):
            if not (r['worlds']==1 and not r['overflowed'] and r['truth_present'] and 2<=r['ply']<=12):continue
            eligible+=1;path=args.cache/r['game']/'replay.json';g=json.loads(path.read_text());b=referee.FowBoard()
            for f in g['frames'][1:r['ply']+1]:b.push_uci(f['move'])
            encoded=''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
            assert encoded==g['frames'][r['ply']]['board'] and int(not b.turn)==r['side']
            key=(encoded,int(b.turn),int(b.castling_rights),b.ep_square,b.halfmove_clock)
            if key not in states:states[key]={'board':b,'origins':[]}
            states[key]['origins'].append(dict(game=r['game'],ply=r['ply'],move=r['move'],source_sha256=sha(path)))
    frozen={'selection':'All exact singleton, truth-supported, uncapped decisions at plies2..12 in the frozen two batches; no result filter.',
        'eligible_decisions':eligible,'unique_positions':len(states),'inputs':sources,
        'labeler_sha256':sha(Path(__file__).with_name('m4_information_dilemma.py')),
        'curator_sha256':sha(Path(__file__)),
        'referee_sha256':sha(Path(referee.__file__)), 'python_chess_version':chess.__version__,
        'scope':'Small structural motif corpus, not a training-scale dataset or a playing-strength benchmark.'}
    (args.out/'manifest.json').write_text(json.dumps(frozen,indent=2)+'\n')
    shutil.copyfile(Path(__file__).with_name('m4_information_dilemma.py'),args.out/'labeler.py')
    shutil.copyfile(__file__,args.out/'curator.py')
    shutil.copyfile(referee.__file__,args.out/'referee.py');summary=[];begin=time.time()
    with (args.out/'move-labels.jsonl').open('w') as rows:
        for key,state in states.items():
            board=state['board'];identifier=hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
            labels=[]
            for move in referee.fow_moves(board):
                label=analyze(board,move,referee,chess);labels.append(label)
                compact={k:v for k,v in label.items() if k not in ['groups','terminal_replies']}
                compact.update(position=identifier,fen=board.fen())
                rows.write(json.dumps(compact)+'\n');rows.flush()
            detail=dict(position=identifier,fen=board.fen(),origins=state['origins'],moves=labels)
            path=args.out/(identifier+'.json.gz');path.write_bytes(gzip.compress(json.dumps(detail).encode(),mtime=0))
            dangerous=[x['move'] for x in labels if x.get('groups_with_no_universal_survival',0)]
            row=dict(position=identifier,fen=board.fen(),origins=state['origins'],actions=len(labels),
                dangerous_setups=dangerous,sha256=sha(path),elapsed_seconds=time.time()-begin)
            summary.append(row);(args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            print(json.dumps({k:v for k,v in row.items() if k!='origins'}),flush=True)
    (args.out/'complete.json').write_text(json.dumps(dict(elapsed_seconds=time.time()-begin,
        positions=len(summary),actions=sum(s['actions'] for s in summary),dangerous_setups=sum(len(s['dangerous_setups']) for s in summary),
        move_labels_sha256=sha(args.out/'move-labels.jsonl')),indent=2)+'\n')


if __name__=='__main__':main()
