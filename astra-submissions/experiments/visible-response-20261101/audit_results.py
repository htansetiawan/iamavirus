#!/usr/bin/env python3
"""Post-fit descriptive slices and checksums; cannot change the gate or model."""
import json
import hashlib
import shutil

import numpy as np

import data


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    frozen=json.loads((data.OUT/'frozen-models.json').read_text())
    decision=json.loads((data.OUT/'decision.json').read_text())
    manifest=json.loads((data.OUT/'manifest.json').read_text())
    results=json.loads((data.OUT/'test-results.json').read_text())
    chosen=frozen['chosen'];scores={}
    dest=data.OUT/'scores';dest.mkdir(exist_ok=True)
    for name,record in frozen['models'].items():
        assert sha(data.BUILD/(name+'.pt'))==record['sha256']
        for split in ['validation','test']:
            path=data.BUILD/(name+'-'+split+'-scores.npz')
            expected=record['predictions']['sha256'] if split=='validation' else results[name]['predictions']['sha256']
            assert sha(path)==expected
            raw=np.load(path)
            target=dest/path.name;assert not target.exists()
            np.savez_compressed(target,**{k:raw[k] for k in raw.files})
            if split=='test':scores[name]={k:raw[k].copy() for k in raw.files}
    reference=scores['linear'];selected=scores[chosen];meta={k:reference[k] for k in ['game','ply','side','team']}
    for other in scores.values():
        for k,v in meta.items():assert np.array_equal(v,other[k])
    novel=np.load(data.BUILD/'test-novel.npy');post8=meta['ply']//2+1>8
    from learning.move_taxonomy import label_game,KEYS
    taxonomy=np.zeros((len(meta['game']),len(KEYS)),dtype=bool)
    game_rows={g['index']:g for g in manifest['games'] if g['split']=='test'}
    for index,g in game_rows.items():
        path=data.ROOT/'data/raw/games'/g['game']/'replay.json';assert sha(path)==g['replay_sha256']
        tags={r['ply']-1:set(r['tags']) for r in label_game(json.loads(path.read_text()))['moves']}
        for row in np.flatnonzero(meta['game']==index):taxonomy[row]=[k in tags[int(meta['ply'][row])] for k in KEYS]
    diff=reference['nll']-selected['nll'];direct_diff=scores['direct']['nll']-selected['nll']
    slices={}
    for name,mask in [('novel_post8',novel&post8),('seen_post8',~novel&post8),
                      *[(k,taxonomy[:,i]&post8) for i,k in enumerate(KEYS)]]:
        if mask.any():slices[name]=dict(n=int(mask.sum()),gain_vs_linear=float(diff[mask].mean()),
                                       gain_vs_direct=float(direct_diff[mask].mean()),selected_nll=float(selected['nll'][mask].mean()))
    np.savez_compressed(dest/'test-taxonomy.npz',tags=taxonomy,keys=np.array(KEYS),novel=novel,**meta)
    result=dict(chosen=chosen,decision_unchanged=decision,
                scope='Descriptive correlated post-fit groups. True-board/future tags are labels only and cannot override the frozen gate.',
                slices=slices,all_raw_prediction_hashes_verified=True,
                frozen_model_file_mtime_before_test_files=(data.OUT/'frozen-models.json').stat().st_mtime <= min((data.BUILD/(name+'-test-scores.npz')).stat().st_mtime for name in scores),
                published_scores={p.name:sha(p) for p in sorted(dest.glob('*.npz'))})
    assert result['frozen_model_file_mtime_before_test_files']
    (data.OUT/'postfit-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='published_scores'},indent=2))


if __name__=='__main__':main()
