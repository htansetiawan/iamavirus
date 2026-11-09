"""Independent artifact/coverage checks after the frozen actor batch closes."""
from collections import defaultdict
import json
from pathlib import Path
import math
import zipfile

from prepare import ROOT,OUT,BUILD,ARCHIVE,sha,write


def main():
    plan=json.loads((OUT/'plan.json').read_text())
    completion=json.loads((OUT/'completion.json').read_text())
    review=json.loads((OUT/'review.json').read_text())
    assert completion['stop']=='completed' and completion['completed']==completion['planned']==72
    for path,digest in plan['dependencies'].items():assert sha(Path(path))==digest,path
    main_source=(BUILD/'src/main.c').read_text()
    anchor='        printf("move %s\\n", uci); fflush(stdout);'
    cut=main_source.index(anchor)+len(anchor)
    end=main_source.index('        clock_left = reported - (now_seconds() - view_at) + increment;',cut)
    with zipfile.ZipFile(ARCHIVE) as z:
        assert main_source[:cut]+ '\n' +main_source[end:]==z.read('src/main.c').decode()
        g=z.read('src/gtcfr.c').decode().replace('#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"')
        free='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
        g=g.replace(free,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+free)
        assert g==(BUILD/'src/gtcfr.c').read_text()
    assert main_source.index('getenv("ASTRA_POST_TRUTH")')>cut
    assert main_source.count('getenv("ASTRA_POST_TRUTH")')==1
    records=[]
    for row in review['rows']:
        assert 'fault' not in row,row
        case=row['case'];seed=row['seed'];folder=OUT/'jobs'/f"{case['id']}-s{seed}"
        result=json.loads((folder/'result.json').read_text())
        for name,digest in result['files'].items():assert sha(folder/name)==digest,(folder,name)
        assert not result['fault'] and not result['live_members']
        chosen=[a for a in row['actions'] if a['chosen']]
        assert len(chosen)==1 and chosen[0]['move']==row['move']
        if row['placement']['matches']==0:assert row['placement']['share']==0
        assert 0<=row['placement']['share']<=1.000000001
        record=dict(case=case['id'],seed=seed,root_export=result['tree_exported'])
        if result['tree_exported']:
            t=json.loads((folder/'tree.jsonl').read_text().splitlines()[0]);actions=t['actions']
            assert t['own_reach_consistent'] and math.isclose(sum(a['probability'] for a in actions),1,abs_tol=1e-9)
            assert set(t['avoid_moves']).isdisjoint(a['uci'] for a in actions)
            assert t['solver_move']==max(actions,key=lambda a:a['probability'])['uci']
            record['frontend_changed_move']=t['solver_move']!=row['move']
            record['safe_kept_missing_from_tree']=sorted(set(row['safe_kept'])-{a['uci'] for a in actions})
        records.append(record)
    assert len(records)==72 and len({(r['case'],r['seed']) for r in records})==72
    result=dict(passed=True,decisions=72,source_edits_only_after_selection=True,
                source_truth_read_only_after_emission=True,all_file_hashes_match=True,
                root_exported=sum(r['root_export'] for r in records),
                frontend_changes=sum(r.get('frontend_changed_move',False) for r in records),
                safe_kept_missing_from_tree=sum(bool(r.get('safe_kept_missing_from_tree')) for r in records),
                records=records,review_sha256=sha(OUT/'review.json'),script_sha256=sha(Path(__file__)))
    write(OUT/'audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
