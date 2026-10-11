#!/usr/bin/env python3
"""Full-information offline oracle for future observation ambiguity.

For each legal own move, group legal opponent replies by our resulting view.
Each view must admit ONE common safe response to give a deterministic guarantee
over that group. This exposes strategy fusion in a per-world escape test. The
known starting board is oracle input, never an input to an arena bot. Counts
are unweighted; they are neither opponent likelihoods nor win-rate estimates.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('replay', type=Path)
    ap.add_argument('--ply', type=int, required=True, help='Position before our candidate move')
    ap.add_argument('--side', choices=['white', 'black'], required=True)
    ap.add_argument('--candidate', nargs='+', help='Omit to enumerate all legal own moves')
    ap.add_argument('--kit', type=Path, default=Path.home()/'git/fow-starter')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    started = time.monotonic()
    game = json.loads(args.replay.read_text())
    color = args.side == 'white'
    loss = '0-1' if color else '1-0'
    board = referee.FowBoard()
    counts = Counter({referee.position_key(board):1})
    if not 0 <= args.ply < len(game['frames'])-1:
        raise ValueError('Selected ply missing')
    for i, frame in enumerate(game['frames'][:args.ply+1]):
        if i:
            move = chess.Move.from_uci(frame['move'])
            if referee.outcome(board, counts) or move not in referee.fow_moves(board):
                raise ValueError('Illegal historical prefix')
            board.push(move); counts[referee.position_key(board)] += 1
        actual = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        if frame['ply'] != i or actual != frame['board']:
            raise ValueError('Historical board mismatch')
        for side, turn in [('white',chess.WHITE),('black',chess.BLACK)]:
            if referee.observation(board,turn) != frame[side]:
                raise ValueError('Historical observation mismatch')
    if board.turn != color or referee.outcome(board,counts):
        raise ValueError('Target is not a nonterminal decision for the selected side')
    candidates = sorted(m.uci() for m in referee.fow_moves(board))
    if args.candidate:
        if not set(args.candidate) <= set(candidates):
            raise ValueError('Illegal requested candidate')
        candidates = sorted(set(args.candidate))
    rows=[]
    for move in candidates:
        parent = board.copy(); parent.push_uci(move)
        after = counts.copy(); after[referee.position_key(parent)] += 1
        ending = referee.outcome(parent,after)
        row={'move':move,'own_outcome':ending,'opponent_replies':0,'groups':[],'opponent_terminal_losses':[]}
        if ending is None:
            groups=defaultdict(list)
            for reply in referee.fow_moves(parent):
                row['opponent_replies'] += 1
                child = parent.copy(); child.push(reply)
                reps=after.copy(); reps[referee.position_key(child)] += 1
                terminal=referee.outcome(child,reps)
                if terminal:
                    if terminal[0] == loss:
                        row['opponent_terminal_losses'].append(reply.uci())
                    continue
                safe=[];legal=[]
                for escape in referee.fow_moves(child):
                    last=child.copy(); last.push(escape)
                    end_counts=reps.copy();end_counts[referee.position_key(last)] += 1
                    outcome=referee.outcome(last,end_counts)
                    legal.append(escape.uci())
                    if outcome is None or outcome[0] != loss:
                        safe.append(escape.uci())
                groups[referee.observation(child,color)].append(
                    {'reply':reply.uci(),'safe':sorted(safe),'legal':sorted(legal)})
            for observation, worlds in sorted(groups.items()):
                common=set.intersection(*(set(w['safe']) for w in worlds))
                individually_safe=all(w['safe'] for w in worlds)
                disjoint=[]
                if individually_safe and not common:
                    disjoint=[(a['reply'],b['reply']) for a,b in itertools.combinations(worlds,2)
                              if not set(a['safe']) & set(b['safe'])]
                row['groups'].append({'observation':observation,'opponent_replies':len(worlds),
                    'common_safe_replies':sorted(common),'every_world_has_a_safe_reply':individually_safe,
                    'information_conflict':individually_safe and not common,
                    'disjoint_pairs':disjoint,'worlds':worlds})
        row['conflict_groups']=sum(g['information_conflict'] for g in row['groups'])
        row['physically_forced_groups']=sum(not g['every_world_has_a_safe_reply'] for g in row['groups'])
        # Empty continuation is safe when every opponent move already ended in
        # a win/draw for us. Do not turn that vacuous guarantee into a failure.
        row['all_groups_have_common_safe_reply']=all(g['common_safe_replies'] for g in row['groups'])
        row['short_horizon_safe']=bool(ending and ending[0]!=loss) or (
            ending is None and not row['opponent_terminal_losses'] and row['all_groups_have_common_safe_reply'])
        rows.append(row)
    result={'created_at':datetime.now(timezone.utc).isoformat(),'game':game['id'],'ply':args.ply,'side':args.side,
            'replay_sha256':sha(args.replay),'referee_sha256':sha(args.kit/'referee.py'),'tool_sha256':sha(Path(__file__)),
            'classification':'truth-started offline information-set oracle; not a belief policy or Elo estimate',
            'scope':'Our candidate, one opponent reply, one view-conditioned own response. Terminal outcomes use exact referee history. No probabilities or later continuation values. A short-horizon guarantee applies only to this starting board.',
            'all_legal_candidates':args.candidate is None,'elapsed_seconds':time.monotonic()-started,'rows':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'elapsed_seconds':result['elapsed_seconds'],'rows':[
        {k:r[k] for k in ['move','opponent_replies','conflict_groups','physically_forced_groups','short_horizon_safe']} for r in rows]},indent=2))


if __name__ == '__main__':
    main()
