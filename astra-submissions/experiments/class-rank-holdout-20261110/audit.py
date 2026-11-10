"""Independent source/course audit before inference; repeats frozen selection."""
import json
from pathlib import Path
import sys
from collect import ROOT, OUT, metadata
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref
from protocol import now, sha, stamp_ns, write, check_pins, cohort_game


def board_text(b):
    return ''.join(b.piece_at(s).symbol() if b.piece_at(s) else '-' for s in range(64))


def main():
    plan=json.loads((OUT/'plan.json').read_text()); check_pins(plan)
    assert json.loads((OUT/'collection.json').read_text())['status']=='complete'
    assert not (OUT/'source-audit.json').exists(), 'one source audit'
    cohort=json.loads((OUT/'cohort.json').read_text()); archive=Path(plan['archive'])
    assert cohort['plan_sha256']==sha(OUT/'plan.json')
    listing=json.loads((OUT/'listing.json').read_text())
    assert cohort['listing_sha256']==sha(OUT/'listing.json')
    merged={}; overlaps=0
    for team in plan['priority']:
        previous=None; terminal=False; cursor=None
        pages=[p for p in listing['pages'] if p['path'].startswith('page-'+team+'-')]
        assert pages
        for index,p in enumerate(pages):
            assert not terminal and p['path'].endswith(f'-{index:02d}.json')
            assert sha(archive/p['path'])==p['sha256']==p['fetch']['sha256']
            from urllib.parse import urlparse,parse_qs
            q=parse_qs(urlparse(p['fetch']['url']).query)
            assert q['player']==[team] and q['sort']==['played'] and q['order']==['desc'] and q['limit']==['100']
            assert q.get('cursor')==([cursor] if cursor else None)
            page=json.loads((archive/p['path']).read_text())
            for row in page['games']:
                assert team in (row['whitePlayerId'],row['blackPlayerId'])
                t=stamp_ns(row['createdAt']); assert previous is None or t<=previous; previous=t
                if stamp_ns(plan['window'][0])<=t<stamp_ns(plan['window'][1]):
                    if row['id'] in merged: assert metadata(merged[row['id']])==metadata(row); overlaps+=1
                    merged[row['id']]=row
            cursor=page['nextCursor']
            terminal=not cursor or (previous is not None and previous<stamp_ns(plan['window'][0]))
        assert terminal, 'source-window coverage'
    ordered=sorted(merged.values(),key=lambda r:(stamp_ns(r['createdAt']),r['id']))
    assert [metadata(r) for r in ordered]==[metadata(r) for r in listing['games']]
    prior=json.loads(Path(plan['exclusions']).read_text())['games']
    deny_ids={g['game'] for g in prior}; deny={g['sequence_sha256'] for g in prior}
    selected=[]; frames_checked=0; actual_moves=0
    for row in ordered:
        if row['id'] in deny_ids or row['plies']<4: continue
        source=archive/(row['id']+'.json'); replay=json.loads(source.read_text())
        assert replay.get('rulesVersion')=='fow-v1'
        g,why=cohort_game(row,replay,sha(source),deny)
        if g is None: assert why=='whole-sequence duplicate'; continue
        g['split']='independent_retrospective_holdout'
        board=ref.FowBoard()
        for ply,frame in enumerate(replay['frames']):
            assert frame['ply']==ply
            if ply:
                move=ref.chess.Move.from_uci(frame['move']); assert move in ref.fow_moves(board)
                board.push(move); actual_moves+=1
            else: assert frame['move'] is None
            assert frame['board']==board_text(board)
            assert frame['white']==ref.observation(board,True) and frame['black']==ref.observation(board,False)
            frames_checked+=1
        selected.append(g); deny.add(g['sequence_sha256'])
        if len(selected)==plan['games']: break
    assert selected==cohort['games'] and len(selected)==plan['games']
    write(OUT/'source-audit.json',dict(at=now(),passed=True,games=len(selected),frames=frames_checked,
          actual_moves=actual_moves,old_trajectory_exclusions=len(prior),overlap_rows=overlaps,
          cohort_sha256=sha(OUT/'cohort.json'),models_opened=False,probabilities_evaluated=False),exclusive=True)
    print('source and course audit passed',len(selected),frames_checked,flush=True)


if __name__=='__main__': main()
