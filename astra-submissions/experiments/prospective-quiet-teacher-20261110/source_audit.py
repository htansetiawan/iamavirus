"""Seal/order/exclusion/course audit before any new teacher scores."""
import json
import importlib.util
from pathlib import Path
import sys
from urllib.parse import parse_qs,urlparse
from protocol import ROOT,OUT,sha,stamp_ns,ordered_candidates,cohort_game,check_pins,now,write
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref
spec=importlib.util.spec_from_file_location('independent_cohort_source',ROOT/'astra-submissions/experiments/cohort-integrity-20261110/audit.py')
independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)


def main():
    plan=json.loads((OUT/'plan.json').read_text());check_pins(plan)
    state=json.loads((OUT/'execution.json').read_text());cohort=json.loads((OUT/'cohort.json').read_text())
    assert state['status']=='complete' and state['phase']=='sealed'
    assert state['cohort_sha256']==sha(OUT/'cohort.json')
    assert stamp_ns(state['started_at'])<stamp_ns(plan['cutoff'])
    assert stamp_ns(plan['cutoff'])<=stamp_ns(cohort['sealed_at'])<=stamp_ns(now())
    assert cohort['no_parameters_loaded_or_predictions_computed'] and not (OUT/'scoring.json').exists()
    archive=Path(plan['archive'])
    tick=json.loads((archive/f"tick-{cohort['collection_tick']:03d}.json").read_text())
    listed,page_hashes=independent.snapshot(archive,cohort['collection_tick'],tick['pages'],plan['cutoff'])
    ordered=independent.candidates(listed,plan)
    denied={g['sequence_sha256'] for g in json.loads(Path(plan['previous_plan']).read_text())['games']}
    rebuilt=[];frames=0;considered=0
    for row in ordered:
        path=archive/'games'/row['id']/'replay.json';rp=json.loads(path.read_bytes());fetch=json.loads(path.with_name('fetch.json').read_text())
        assert sha(path)==fetch['sha256']
        g,reason=independent.reconstruct(row,rp,sha(path),denied,set(plan['teams']));considered+=1
        if g is None:continue
        denied.add(g['sequence_sha256']);rebuilt.append(g);board=ref.FowBoard()
        for ply,frame in enumerate(rp['frames']):
            if ply:
                move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(board);board.push(move)
            full=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
            assert frame['ply']==ply and frame['board']==full
            assert frame['white']==ref.observation(board,True) and frame['black']==ref.observation(board,False)
            frames+=1
        if len(rebuilt)==plan['games']:break
    assert rebuilt==cohort['games'] and len(rebuilt)==plan['games']
    report=dict(passed=True,at=now(),games=len(rebuilt),considered=considered,source_frames=frames,source_pages=tick['pages'],
        cohort_sha256=sha(OUT/'cohort.json'),preexisting_exclusions=len(json.loads(Path(plan['previous_plan']).read_text())['games']),
        teacher_predictions_opened=False,limitation='Independent existing298snapshot/eligibility/reconstruction code plus course-frame audit; collector selection helpers are not used. Native and typed input checks occur in the separately pinned producer before inference.')
    write(OUT/'source-audit.json',report,exclusive=True);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
