"""Aggregate oracle motifs by piece-role relationships, never team identity."""
from collections import defaultdict
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/terminal-motifs-20261110'
plan=json.loads((OUT/'plan.json').read_text());rows=json.loads((Path(plan['private'])/'rows.json').read_text());groups=defaultdict(list)
for row in rows:
    event=row['terminal_motif']
    if event is None:continue
    key=(event['kind'],event['victim_piece'],''.join(sorted({k['piece'] for k in event['killers']})),event['already_attacked'],event['all_killers_hidden'],event['forced_one_ply_loss'])
    groups[key].append(row)
patterns=[dict(kind=k[0],victim=k[1],guard_types=k[2],already_attacked=k[3],all_guards_hidden=k[4],forced_one_ply=k[5],
    terminal_occurrences=len(v),distinct_games=len({r['id'] for r in v}),different_teams=len({r['team_id'] for r in v}))
    for k,v in sorted(groups.items(),key=lambda p:(-len(p[1]),str(p[0])))]
result=dict(patterns=patterns,terminal_occurrences=sum(p['terminal_occurrences'] for p in patterns),
    source_rows_sha256=hashlib.sha256((Path(plan['private'])/'rows.json').read_bytes()).hexdigest(),
    schema='oracle piece-role motif facets v1',scope='Descriptive terminal-only pattern aggregation, not a learned vocabulary, actor feature or acceptance-rate estimate. Full opportunity denominators are separate in result.json. Existing011actor-onlySQLite retrieval must not ingest these privileged labels as actor inputs.')
with (OUT/'pattern-summary.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Identity-free pattern facets:',len(patterns),'terminal events:',result['terminal_occurrences'])
