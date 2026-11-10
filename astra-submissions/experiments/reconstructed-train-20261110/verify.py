"""Read-only verification from packed actions; never reruns a model or builder."""
import hashlib
import json
import signal
import time
from build import OUT,SOURCE,codec,ref,board_text,now,sha,write
from experience_index import unpack_view


def main():
    begin=time.monotonic();plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('verification bound')));signal.alarm(plan['verify_seconds'])
    source=json.loads(SOURCE.read_text());expected=[g for g in source['games'] if g['split']=='train']
    cache=codec.Cache(plan['cache']);frames=actions=0
    try:
        assert len(cache.games)==len(expected)==4000
        for original,g in zip(expected,cache.games):
            assert g['game']==original['game'] and g['start']==frames and g['records']==original['frames']
            assert g['original_split']=='train' and not g['clocks_available'] and not g['recorded_result_available']
            b=ref.FowBoard();moves=[]
            for ply in range(g['records']):
                raw=cache.record(g['start']+ply);row=codec.fields(raw)
                assert unpack_view(row[0])==board_text(b)
                assert [codec.actor_view(raw,s) for s in (0,1)]==[ref.observation(b,True),ref.observation(b,False)]
                assert row[3:7]==(int(b.clean_castling_rights()),b.ep_square if b.ep_square is not None else -1,b.halfmove_clock,0 if b.turn else 1)
                selection=(1 if ply in original['selected_plies'] else 0)|(2 if original[('white','black')[ply%2]] in source['teams'] else 0)|(4 if ply//2>=8 else 0)
                assert row[8]==selection
                text=codec.decode_move(row[7]);flags=0
                if ply==g['records']-1:assert text is None and row[9]==0
                else:
                    assert text==original['moves'][ply];move=ref.chess.Move.from_uci(text);assert move in ref.fow_moves(b)
                    flags|=1 if b.is_capture(move) else 0;flags|=2 if b.is_en_passant(move) else 0
                    flags|=4 if b.is_castling(move) else 0;flags|=8 if move.promotion else 0
                    mover=b.turn;b.push(move);king=b.king(mover)
                    flags|=16 if king is None or b.is_attacked_by(not mover,king) else 0
                    assert row[9]==flags;moves.append(text);actions+=1
                frames+=1
            assert hashlib.sha256(' '.join(moves).encode()).hexdigest()==original['sequence_sha256']==g['sequence_sha256']
        assert frames==plan['records'] and actions==plan['moves']
        write(OUT/'independent-review.json',dict(at=now(),passed=True,games=len(expected),frames=frames,actions=actions,seconds=time.monotonic()-begin,
              source_plan_sha256=sha(SOURCE),cache_manifest_sha256=sha(cache.folder/'manifest.json'),models_fitted=False,api_requests=0,
              scope='Full read-only packed-action/source-sequence reconstruction and course-state validation; build separately checked native C agreement. No learning or strength evidence.'))
        print('independent packed cache verification passed',frames,actions,flush=True)
    finally:cache.close();signal.alarm(0)


if __name__=='__main__':main()
