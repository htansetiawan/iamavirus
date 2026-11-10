"""Independent raw-count and terminal geometry aggregation; no inference."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from labels import ROOT,chess

OUT=ROOT/'astra-submissions/analysis/terminal-motifs-20261110'
VALUE=dict(p=1,n=3,b=3,r=5,q=9,k=0)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    execution=json.loads((OUT/'execution.json').read_text());assert execution['status']=='complete' and execution['own_lease_released']
    for path,expected in plan['dependencies'].items():assert sha(path)==expected,path
    path=Path(plan['private'])/'rows.json';assert sha(path)==result['private_rows_sha256'];rows=json.loads(path.read_text())
    games={g['game']:g for g in json.loads(Path(plan['cohort']).read_text())['games']}
    assert len(games)==300 and len(rows)==600
    assert len({(r['id'],r['side']) for r in rows})==600
    panels={(p['team_id'],p['version']):p for p in result['panels']};groups=defaultdict(list);terminals=0
    for r in rows:
        g=games[r['id']];side=r['side'];rp_path=Path(plan['raw'])/r['id']/'replay.json';rp=json.loads(rp_path.read_text())
        assert sha(rp_path)==r['source_sha256']==g['replay_sha256']
        assert r['team_id']==rp[side+'PlayerId'] and r['version']==rp[side+'Version'] and r['team']==rp[side]
        expected=.5 if rp['result']=='1/2-1/2' else float((rp['result']=='1-0')==(side=='white'))
        assert r['score']==expected
        event=r['terminal_motif'];assert (event is not None)==(expected==0 and rp['reason']=='King capturable')
        if event:
            n=len(rp['frames'])-1;before=rp['frames'][-2]['board'];text=rp['frames'][-1]['move'];source=chess.parse_square(text[:2]);dest=chess.parse_square(text[2:4])
            piece=before[source].lower();capture=before[dest]!='-';king=piece=='k';castle=king and abs(dest-source)==2
            expected_kind='castle_into_attack' if castle else 'king_bait' if king and capture else 'king_walk' if king else 'ignored_check' if event['already_attacked'] else 'opened_king_line'
            assert event['kind']==expected_kind and event['move']==text
            assert event['safe_moves']==sorted(set(r['terminal']['safe_moves']))
            assert event['forced_one_ply_loss']==(len(event['safe_moves'])==0)
            assert event['all_killers_hidden']==all(k['hidden_before'] for k in event['killers'])
            assert all(k['hidden_before']==(rp['frames'][-2][side][chess.parse_square(k['square'])]=='?') for k in event['killers'])
            margin=sum(VALUE[c.lower()]*(1 if c.isupper()==(side=='white') else -1) for c in before if c!='-')
            assert event['material_before']==margin;terminals+=1
        for offer in r['offers']:
            assert offer['avoidable']==bool(offer['safe_moves'])
            if offer['taken']:
                assert event and event['kind']=='king_bait' and offer['ply']==r['plies'] and offer['move']==event['move']
                assert event['all_killers_hidden']
        groups[(r['team_id'],r['version'])].append(r)
    assert set(groups)==set(panels)
    for key,seats in groups.items():
        panel=panels[key];events=[r['terminal_motif'] for r in seats if r['terminal_motif']]
        assert panel['games']==len(seats)
        assert panel['wdl']==dict(Counter('W' if r['score']==1 else 'D' if r['score']==.5 else 'L' for r in seats))
        assert panel['motif_kinds']==dict(Counter(e['kind'] for e in events))
        assert panel['terminal_games']==len(events)
        assert panel['one_ply_forced']==sum(e['forced_one_ply_loss'] for e in events)
        assert panel['hidden_nonforced']==sum(e['all_killers_hidden'] and not e['forced_one_ply_loss'] for e in events)
        assert panel['material_down3_before_fatal']==sum(e['material_before']<=-3 for e in events)
        for bucket,counts in panel['bait'].items():
            typ,piece=bucket.split('/');all_offers=[(r,e) for r in seats for e in r['offers'] if (piece=='all' or e['piece']==piece) and (typ=='all' or e['check']==(typ=='check'))]
            optional=[(r,e) for r,e in all_offers if e['avoidable']]
            assert counts==dict(offers=len(optional),taken=sum(e['taken'] for r,e in optional),games=len({r['id'] for r,e in optional}),taken_games=len({r['id'] for r,e in optional if e['taken']}),unavoidable_offers=sum(not e['avoidable'] for r,e in all_offers),unavoidable_taken=sum(not e['avoidable'] and e['taken'] for r,e in all_offers))
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,source_pins=len(plan['dependencies']),games=300,seats=600,terminal_events=terminals,
        panels=len(panels),result_sha256=sha(OUT/'result.json'),review_source_sha256=sha(Path(__file__)),
        limitation='Independent source identities, stored counts, material, geometry category and full offer-denominator aggregation. Referee/C safe-set and attacker-geometry checks come from the original pinned run; this is not an independent policy or inference experiment. Rich labels remain local.')
    with (OUT/'independent-review.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
