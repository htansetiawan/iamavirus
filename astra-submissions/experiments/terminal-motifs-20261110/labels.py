"""Oracle retrospective terminal motifs, independent of player identity."""
from collections import Counter
import ctypes as C
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT.parent/'fow-starter'),str(ROOT/'astra-submissions/tools')]
import chess
import referee as ref
from analyze_mist import board_string,safe_moves


class Native:
    def __init__(self):
        path=ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so'
        self.lib=C.CDLL(str(path),mode=C.RTLD_LOCAL)
        self.lib.astra_test_set.argtypes=[C.c_char_p,C.c_int,C.c_uint64,C.c_int,C.c_int]
        self.lib.astra_test_step.argtypes=[C.c_uint16]

    def safe(self,board):
        result=[]
        for move in ref.fow_moves(board):
            assert self.lib.astra_test_set(board_string(board).encode(),0 if board.turn else 1,
                int(board.clean_castling_rights()),board.ep_square if board.ep_square is not None else -1,board.halfmove_clock)==0
            promotion='pnbrqk'.index(move.uci()[4]) if move.promotion else 6
            code=move.from_square|(move.to_square<<6)|(promotion<<12)
            status=self.lib.astra_test_step(code);assert status>=0
            if status==0:result.append(move.uci())
        return sorted(result)


def terminal(board,move,native,repetitions=None):
    color=board.turn;view=ref.observation(board,color)
    repetitions=repetitions or Counter({ref.position_key(board):1})
    assert ref.outcome(board,repetitions) is None
    assert move in ref.fow_moves(board)
    piece=board.piece_at(move.from_square);king_before=board.king(color)
    was_attacked=board.is_attacked_by(not color,king_before)
    after=board.copy(stack=False);after.push(move);king=after.king(color)
    assert king is not None and after.is_attacked_by(not color,king)
    kind=('castle_into_attack' if board.is_castling(move) else
          'king_bait' if piece.piece_type==chess.KING and board.is_capture(move) else
          'king_walk' if piece.piece_type==chess.KING else
          'ignored_check' if was_attacked else 'opened_king_line')
    post_view=ref.observation(after,color);killers=[]
    for square in after.attackers(not color,king):
        before_blockers=board.occupied&chess.between(king,square)
        after_blockers=after.occupied&chess.between(king,square)
        killers.append(dict(piece=after.piece_at(square).symbol().upper(),square=chess.square_name(square),
            hidden_before=view[square]=='?',hidden_after=post_view[square]=='?',
            own_screen_released=piece.piece_type!=chess.KING and bool(before_blockers&chess.BB_SQUARES[move.from_square]) and not after_blockers))
    safe=sorted(safe_moves(board));assert safe==native.safe(board)
    # Only the candidate's current repetition key is read by outcome().
    # An O(1) history lookup avoids copying the whole prefix per candidate.
    # Native royal safety must equal exact one-ply non-loss, including draws.
    for candidate in ref.fow_moves(board):
        trial=board.copy(stack=False);trial.push(candidate)
        key=ref.position_key(trial)
        result=ref.outcome(trial,Counter({key:repetitions.get(key,0)+1}))
        loss='0-1' if color else '1-0'
        assert (candidate.uci() in safe)==(result is None or result[0]!=loss)
    victim=board.piece_at(move.to_square)
    value={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
    material=lambda b:sum(v*(len(b.pieces(t,color))-len(b.pieces(t,not color))) for t,v in value.items())
    return dict(kind=kind,move=move.uci(),already_attacked=was_attacked,killers=killers,
        safe_moves=safe,forced_one_ply_loss=not safe,all_killers_hidden=all(k['hidden_before'] for k in killers),
        victim_piece=victim.symbol().upper() if victim else None,
        material_before=material(board),material_after=material(after),
        classification='True-world one-ply survival and current-view geometry only; not a fog-realizable escape or winning policy.')
