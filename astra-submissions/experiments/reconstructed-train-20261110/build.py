"""Recover deterministic training state from pinned move lists; no API/model."""
import ctypes as C
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/reconstructed-train-20261110'
SOURCE=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
sys.path[:0]=[str(ROOT/'astra-submissions/tools'),str(ROOT.parent/'fow-starter')]
import reconstructed_cache as codec
from experience_index import unpack_view
import referee as ref


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def board_text(b):return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))
def native_move(s):
    sq=lambda x:ord(x[0])-97+8*(int(x[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)


class Native:
    def __init__(self,path):
        self.lib=C.CDLL(str(path),mode=C.RTLD_LOCAL)
        self.lib.astra_test_set.argtypes=[C.c_char_p,C.c_int,C.c_uint64,C.c_int,C.c_int]
        self.lib.astra_test_state.argtypes=[C.c_char_p]*3+[C.POINTER(C.c_uint64),C.POINTER(C.c_int),C.POINTER(C.c_int)]
        self.lib.astra_test_step.argtypes=[C.c_uint16]
        self.buffers=[C.create_string_buffer(65) for _ in range(3)]
        self.castle=C.c_uint64();self.ep=C.c_int();self.half=C.c_int()

    def start(self):
        b=ref.FowBoard()
        assert self.lib.astra_test_set(board_text(b).encode(),0,int(b.clean_castling_rights()),-1,0)==0

    def check(self,b,views):
        side=self.lib.astra_test_state(*self.buffers,C.byref(self.castle),C.byref(self.ep),C.byref(self.half))
        assert side==(0 if b.turn else 1)
        assert [v.value.decode() for v in self.buffers]==[board_text(b),*views]
        assert (self.castle.value,self.ep.value,self.half.value)==(int(b.clean_castling_rights()),b.ep_square if b.ep_square is not None else -1,b.halfmove_clock)


def prepare():
    OUT.mkdir(exist_ok=False)
    original=json.loads(SOURCE.read_text());games=[g for g in original['games'] if g['split']=='train']
    assert len(games)==len({g['game'] for g in games})==len({g['sequence_sha256'] for g in games})==4000
    assert all(g['frames']==len(g['moves'])+1 for g in games)
    native=HERE.parent/'observed-class-20261110/build/producer.so'
    deps=[HERE/'build.py',HERE/'verify.py',ROOT/'astra-submissions/tools/reconstructed_cache.py',
          ROOT/'astra-submissions/tools/experience_index.py',ROOT/'astra-submissions/tools/test_reconstructed_cache.py',
          SOURCE,ROOT.parent/'fow-starter/referee.py',native,
          HERE.parent/'observed-class-20261110/producer.c',HERE.parent/'observation-rank-20261110/rank.c']
    ship=HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
    deps+=list((ship/'src').glob('*'))
    plan=dict(at=now(),source=str(SOURCE),source_sha256=sha(SOURCE),native=str(native),cores=[2,3],
        cache=str(ROOT/'data/astra-spool/reconstructed-train-20261110'),max_seconds=600,verify_seconds=600,max_bytes=64*1024*1024,
        games=4000,records=sum(g['frames'] for g in games),moves=sum(len(g['moves']) for g in games),
        expected_record_bytes=codec.ROW.size*sum(g['frames'] for g in games),record_size=codec.ROW.size,
        scope='Infrastructure reconstruction of exactly4000 old293 TRAIN traces, preserving original order, moves and metadata. '
              'Only TRAIN trajectories are materialized; no old validation/test or current307 trajectory is processed, scored or fitted. '
              '011 already implements lossless nibble packing; reuse that codec. This adds typed64-byte world records, causal actor projection and recovery from frozen move lists. '
              'Not restored raw replays, an independent test set, a model, strength estimate or new compression algorithm. Clocks and recorded outcomes remain absent; no fabricated defaults.',
        validation='Every reconstructed full board, both observations and castling/EP/halfmove/side must match independent C/course engines; '
                   'actual moves legal in both; source trajectory hashes/selected masks preserved; streaming packed decode and separate full read-only verifier. '
                   'Actor interface omits opponent/current moves, full truth, flags, names and world metadata; hidden-cell privacy and special-move codec tests.',
        publish='Cache loader accepts only the complete manifest after data/index fsync and hashes. Partial failures remain marked and unpublished. '
                'Private bounded working cache on root SSD while Seagate is unavailable; cold storage of record is unchanged. No symlink replacement, API, watcher, GPU, fit, candidate/ZIP or arena action.',
        dependencies={str(p):sha(p) for p in sorted(set(deps))})
    assert plan['expected_record_bytes']<plan['max_bytes']
    write(OUT/'plan.json',plan);print(json.dumps(dict(prepared=True,games=plan['games'],records=plan['records'],bytes=plan['expected_record_bytes'])),flush=True)


def collect():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert not (OUT/'execution.json').exists(),'one original build attempt'
    os.sched_setaffinity(0,set(plan['cores']))
    cache=Path(plan['cache']);cache.mkdir(exist_ok=False)
    original=json.loads(SOURCE.read_text());games=[g for g in original['games'] if g['split']=='train']
    native=Native(plan['native']);index=[];rows=0;selected=references=fatals=0;begin=time.monotonic()
    state=dict(at=now(),status='running',plan_sha256=sha(OUT/'plan.json'));write(OUT/'execution.json',state)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('cache build bound')));signal.alarm(plan['max_seconds'])
    try:
        with (cache/'records.bin').open('xb') as target:
            for number,g in enumerate(games):
                assert hashlib.sha256(' '.join(g['moves']).encode()).hexdigest()==g['sequence_sha256']
                b=ref.FowBoard();native.start();wanted=set(g['selected_plies']);assert all(0<=p<len(g['moves']) for p in wanted)
                start=rows
                for ply,text in enumerate([*g['moves'],None]):
                    views=[ref.observation(b,True),ref.observation(b,False)];native.check(b,views)
                    side=0 if b.turn else 1;flags=0;next_b=None
                    selection=(codec.SELECTED if ply in wanted else 0)|(codec.REFERENCE if g[('white','black')[side]] in original['teams'] else 0)|(codec.AFTER_EIGHT if ply//2>=8 else 0)
                    if text is not None:
                        move=ref.chess.Move.from_uci(text);assert move in ref.fow_moves(b)
                        flags=(codec.CAPTURE if b.is_capture(move) else 0)|(codec.EN_PASSANT if b.is_en_passant(move) else 0)|(codec.CASTLE if b.is_castling(move) else 0)|(codec.PROMOTION if move.promotion else 0)
                        next_b=b.copy(stack=False);next_b.push(move);king=next_b.king(b.turn)
                        fatal=king is None or next_b.is_attacked_by(not b.turn,king)
                        flags|=codec.FATAL if fatal else 0
                        assert native.lib.astra_test_step(native_move(text))==int(fatal)
                    raw=codec.encode(board_text(b),*views,int(b.clean_castling_rights()),b.ep_square if b.ep_square is not None else -1,b.halfmove_clock,side,text,selection,flags)
                    assert unpack_view(codec.fields(raw)[0])==board_text(b)
                    assert [codec.actor_view(raw,s) for s in (0,1)]==views
                    target.write(raw);rows+=1;assert rows*codec.ROW.size<=plan['max_bytes']
                    selected+=int(bool(selection&codec.SELECTED));references+=int(text is not None and bool(selection&codec.REFERENCE));fatals+=int(bool(flags&codec.FATAL))
                    if next_b is not None:b=next_b
                native.check(b,[ref.observation(b,True),ref.observation(b,False)])
                index.append(dict(game=g['game'],original_split='train',start=start,records=rows-start,moves=len(g['moves']),
                    sequence_sha256=g['sequence_sha256'],original_replay_sha256=g['replay_sha256'],created_at=g['created_at'],
                    white=g['white'],black=g['black'],white_version=g['white_version'],black_version=g['black_version'],
                    selected_plies=g['selected_plies'],clocks_available=False,recorded_result_available=False))
                if (number+1)%250==0:print(json.dumps(dict(games=number+1,records=rows)),flush=True)
            target.flush();os.fsync(target.fileno())
        assert rows==plan['records'] and len(index)==plan['games']
        write(cache/'games.json',index)
        with (cache/'games.json').open('rb') as handle:os.fsync(handle.fileno())
        assert sum(p.stat().st_size for p in cache.iterdir())<=plan['max_bytes']
        manifest=dict(schema=codec.SCHEMA,record_size=codec.ROW.size,record_format=codec.ROW.format,records=rows,games=len(index),
            original_split='train',source_plan=str(SOURCE),source_plan_sha256=sha(SOURCE),plan_sha256=sha(OUT/'plan.json'),
            clocks_available=False,recorded_result_available=False,raw_replay_recovery=False,
            sha256={n:sha(cache/n) for n in ('records.bin','games.json')},scope=plan['scope'])
        write(cache/'manifest.prepared.json',manifest);os.replace(cache/'manifest.prepared.json',cache/'manifest.json')
        write(OUT/'cache-manifest.json',manifest)
        state.update(status='complete',games=len(index),records=rows,selected=selected,reference_actions=references,fatal_actions=fatals,manifest_sha256=sha(cache/'manifest.json'),cache_bytes=sum(p.stat().st_size for p in cache.iterdir()))
    except BaseException as exc:state.update(status='failed',error=repr(exc),completed_games=len(index),records=rows);raise
    finally:
        signal.alarm(0);state.update(ended_at=now(),seconds=time.monotonic()-begin)
        (OUT/'execution.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state),flush=True)


if __name__=='__main__':globals()[sys.argv[1]]()
