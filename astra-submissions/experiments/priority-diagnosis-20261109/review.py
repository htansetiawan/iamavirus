"""Join emitted decisions with hidden labels after all actor work finishes."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import re

from prepare import OUT,sha,write


def main():
    plan=json.loads((OUT/'plan.json').read_text());counts=defaultdict(Counter);rows=[]
    for seed in plan['seeds']:
        for case in plan['cases']:
            directory=OUT/'jobs'/f"{case['id']}-s{seed}"
            if not (directory/'result.json').exists():continue
            result=json.loads((directory/'result.json').read_text())
            if result['fault']:rows.append(dict(case=case,seed=seed,fault=result['fault']));continue
            text=(directory/'stderr.txt').read_text()
            match=re.search(r'astra: placement count=(\d+) matches=(\d+) share=(\S+) rank=(\d+) capped=(\d+)',text)
            assert match
            placement=dict(count=int(match[1]),matches=int(match[2]),share=float(match[3]),rank=int(match[4]),capped=bool(int(match[5])))
            actions=[]
            for m in re.finditer(r'astra: action (\S+) excluded=(\d+) king=(\S+)/(\S+) queen=(\S+)/(\S+) chosen=(\d+)',text):
                actions.append(dict(move=m[1],excluded=bool(int(m[2])),king=float(m[3]),king_sharp=float(m[4]),queen=float(m[5]),queen_sharp=float(m[6]),chosen=bool(int(m[7]))))
            safe=set(result['truth_safe_moves'])
            safe_in_view=[a['move'] for a in actions if a['move'] in safe]
            kept=[a['move'] for a in actions if a['move'] in safe and not a['excluded']]
            trees=[json.loads(line) for line in (directory/'tree.jsonl').read_text().splitlines()] if result['tree_exported'] else []
            sampled=False
            if trees:
                assert len(trees)==1
                truth=json.loads(Path(case['replay_path']).read_text())['frames'][case['ply']]['board']
                sampled=any(w['hypothesis_board']==truth for w in trees[0]['samples'])
                for a in actions:
                    t=next((t for t in trees[0]['actions'] if t['uci']==a['move']),None)
                    if t:a.update(probability=t['probability'],q=t['q'])
            row=dict(case=case,seed=seed,move=result['move'],fatal=result['fatal'],placement=placement,
                     truth_placement_sampled=sampled,safe_legal_count=len(safe),safe_in_view=safe_in_view,safe_kept=kept,actions=actions,
                     readout_seconds_included_in_runtime=result['elapsed'])
            c=counts[(case['opponent'],case['kind'])];c['decisions']+=1;c['fatal']+=bool(result['fatal']);c['placement_absent']+=not bool(placement['matches'])
            c['placement_present_but_not_sampled']+=bool(placement['matches']) and not sampled
            c['safe_exists']+=bool(safe)
            c['all_safe_absent_from_view']+=bool(safe) and not bool(safe_in_view)
            c['all_safe_excluded']+=bool(safe_in_view) and not bool(kept)
            c['fatal_despite_safe_kept']+=bool(result['fatal']) and bool(kept)
            rows.append(row)
    result=dict(plan_sha256=sha(OUT/'plan.json'),counts=[dict(opponent=k[0],kind=k[1],**v) for k,v in counts.items()],rows=rows,
                scope='Post-hoc forced-prefix diagnostics; placement matches omit rights. Counts are decisions across seeds, not independent games or causal strength estimates.')
    write(OUT/'review.json',result);print(json.dumps(result['counts'],indent=2))


if __name__=='__main__':main()
