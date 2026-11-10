"""C/course-checked hypothetical-world inputs; actual action stays metadata only."""
import ctypes as C
import importlib.util
from pathlib import Path
import sys

import numpy as np
import torch

from protocol import ROOT,OLD
sys.path[:0]=[str(OLD),str(ROOT.parent/'fow-starter'),str(ROOT/'astra-submissions/tools')]
from prepare import library
from prior_training_cache import cache_move
import referee as ref
spec=importlib.util.spec_from_file_location('structural_native',OLD.parent/'reconstructed-train-20261110/build.py')
structural=importlib.util.module_from_spec(spec);spec.loader.exec_module(structural)


class Producer:
    def __init__(self,native_path):
        self.lib=library();self.native=structural.Native(native_path)
        self.buffers=[C.create_string_buffer(65) for _ in range(3)]
        self.moves=np.zeros(256,np.uint16);self.x=np.zeros((256,26),np.float32)
        self.full=np.zeros(256,np.float32);self.cheap=np.zeros(256,np.float32)
        self.counts=np.zeros(256,np.uint32);self.total=C.c_uint();self.surprise=np.zeros(256,np.uint8)

    def game(self,g,replay=None):
        board=ref.FowBoard();self.native.start();self.lib.prior_start();wanted=set(g['selected_plies'])
        assert len(g['moves'])+1==g['frames']
        for ply in range(g['frames']):
            full=structural.board_text(board);views=[ref.observation(board,True),ref.observation(board,False)]
            self.native.check(board,views)
            assert self.lib.prior_state(*self.buffers)==ply%2
            assert [b.value.decode() for b in self.buffers]==[full,*views]
            if replay is not None:
                frame=replay['frames'][ply]
                assert (frame['ply'],frame['board'],frame['white'],frame['black'])==(ply,full,*views)
                assert frame['move']==(g['moves'][ply-1] if ply else None)
            if ply==len(g['moves']):break
            text=g['moves'][ply];action=structural.native_move(text)
            move=ref.chess.Move.from_uci(text);assert move in ref.fow_moves(board)
            if ply in wanted:
                n=self.lib.quiet_features(self.moves,self.x,self.full,self.cheap,self.counts,C.byref(self.total),self.surprise)
                where=np.flatnonzero(self.moves[:n]==action);assert 0<n<=256 and len(where)==1
                target=int(where[0]);assert int(self.counts[:n].sum())<=self.total.value
                piece=np.array(['-PNBRQKpnbrqk'.index(c) for c in full],np.int64)
                visibility=np.array([(1 if views[0][s]!='?' else 0)+(2 if views[1][s]!='?' else 0) for s in range(64)],np.int64)
                castle=np.array([(int(board.clean_castling_rights())>>s)&1 for s in range(64)],np.int64)
                ep=np.array([board.ep_square==s for s in range(64)],np.int64)
                parent=[piece,visibility,castle,ep,np.float32(board.halfmove_clock),np.int64(ply%2)]
                inputs=dict(board=parent,x=self.x[:n].copy(),base=self.full[:n].copy(),counts=self.counts[:n].astype(np.float32),
                    native_moves=self.moves[:n].copy(),moves=np.array([cache_move(int(m)) for m in self.moves[:n]],np.int64),history_n=np.float32(self.total.value))
                metadata=dict(game=g['game'],ply=ply,target=target,primary=ply//2>=8 and not bool(self.x[target,22]),
                    capture=bool(self.x[target,0]),surprise=bool(self.surprise[target]),self_capturable=bool(self.x[target,22]),
                    team_id=g.get(('white_id','black_id')[ply%2]),team=g[('white','black')[ply%2]],
                    version=g.get(('white_version','black_version')[ply%2]))
                yield inputs,metadata
            # Executed only when the consumer advances: this target action was
            # never included among the preceding neural inputs.
            assert self.lib.prior_step(action)>=0
            assert self.native.lib.astra_test_step(action)>=0
            board.push(move)


def batch(rows):
    width=max(len(r['moves']) for r in rows);n=len(rows)
    x=np.zeros((n,width,26),np.float32);base=np.zeros((n,width),np.float32)
    counts=np.zeros((n,width),np.float32);moves=np.zeros((n,width),np.int64);valid=np.zeros((n,width),bool)
    for i,row in enumerate(rows):
        k=len(row['moves']);x[i,:k]=row['x'];base[i,:k]=row['base'];counts[i,:k]=row['counts'];moves[i,:k]=row['moves'];valid[i,:k]=True
    return dict(board=[torch.from_numpy(np.asarray([r['board'][i] for r in rows])) for i in range(6)],x=torch.from_numpy(x),base=torch.from_numpy(base),
        counts=torch.from_numpy(counts),moves=torch.from_numpy(moves),valid=torch.from_numpy(valid),capture=torch.from_numpy(x[:,:,0]>0),
        history_n=torch.tensor([r['history_n'] for r in rows]))
