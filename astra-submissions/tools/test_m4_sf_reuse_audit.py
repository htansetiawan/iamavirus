from m4_sf_reuse_audit import requests,summarize
fen='8/8/8/8/8/8/4k3/6K1 w - - 0 1'
text=f'''>> position fen {fen}
>> go depth 1
<< info depth 1 multipv 1 score cp 10 nodes 20 time 2 pv g1h1
<< info depth 1 multipv 2 score mate -3 nodes 20 time 2 pv g1f1
<< bestmove g1h1
>> position fen {fen}
>> go depth 1
<< info depth 1 multipv 1 score cp 40 nodes 20 time 3 pv g1h1
<< info depth 1 multipv 2 score mate -3 nodes 20 time 3 pv g1f1
<< bestmove g1h1
'''
r=list(requests(text.splitlines()));assert len(r)==2
assert r[0]['scores']=={'g1h1':10,'g1f1':-19700}
s=summarize(r);assert s['repeat_share']==.5 and s['changed_score_maps_on_repeat']==1
assert s['absolute_cp_change_vs_first']['max']==30 and s['engine_reported_ms_on_repeats']==3
assert s['absolute_cp_change_vs_first']['median']==15
assert summarize([r[0],r[0]])['identical_score_maps_on_repeat']==1
for bad in [text.rsplit('<< bestmove',1)[0], '>> go depth 1\n',text.replace('go depth 1','go depth 2',1)]:
 try:list(requests(bad.splitlines()))
 except ValueError:pass
 else:raise AssertionError('invalid or truncated trace accepted')
print('test_m4_sf_reuse_audit: exact repeats, score changes, mate conversion, request pairing and truncated capture passed')
