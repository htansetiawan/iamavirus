"""Exploratory read-only count of necessary regret updates at saved profiles.

This does not implement Lazy-CFR or change the measured performance gate.
"""
from pathlib import Path
import hashlib,json,struct,statistics
import numpy as np
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(path):
 raw=Path(path).read_bytes();assert raw[:8]==b'ASTRA253';nn,ne,ni,ns,root=struct.unpack_from('=5i',raw,8)
 dtype=np.dtype([('type','=i4'),('player','=i4'),('info','=i4'),('first','=i4'),('count','=i4'),('value','=f8')]);assert dtype.itemsize==28
 nodes=np.frombuffer(raw,dtype=dtype,count=nn,offset=28);at=28+28*nn
 def take(dtype,count):
  nonlocal at
  x=np.frombuffer(raw,dtype=dtype,count=count,offset=at);at+=x.nbytes;return x
 child=take('=i4',ne);prob=take('=f8',ne);player=take('=i4',ni);actions=take('=i4',ni);offset=take('=i4',ni);regret=take('=f8',ns);last=take('=f8',ns);average=take('=f8',ns);assert at==len(raw)
 x=np.maximum(regret+last,0).copy();previous=set()
 for I,o in enumerate(offset):
  n=actions[I];total=x[o:o+n].sum();x[o:o+n]=x[o:o+n]/total if total>0 else 1/n
  if np.any(last[o:o+n]!=0):previous.add(I)
 rows=[]
 for p in (0,1):
  active=set();visited=set();todo=[root]
  while todo:
   node=todo.pop()
   if node in visited:continue
   visited.add(node);r=nodes[node];t=int(r['type']);o=int(r['first']);n=int(r['count'])
   if t==2:continue
   if t==0:todo.extend(int(child[o+a]) for a in range(n) if prob[o+a]>0)
   else:
    I=int(r['info']);start=int(offset[I])
    if int(r['player'])==p:active.add(I);todo.extend(int(c) for c in child[o:o+n])
    else:todo.extend(int(child[o+a]) for a in range(n) if x[start+a]>0)
  pending=active|{I for I in previous if player[I]==p};total=int(actions[player==p].sum())
  rows.append(dict(player=p,visited_nodes=len(visited),total_nodes=nn,total_action_slots=total,visited_infosets=len(active),visited_action_slots=int(sum(actions[I] for I in active)),update_or_clear_prediction_slots=int(sum(actions[I] for I in pending)),fraction_required=float(sum(actions[I] for I in pending)/total)))
 return rows
def main():
 receipt=json.loads((OUT/'receipt.json').read_text());assert receipt['state']=='completed';rows=[]
 for job in receipt['jobs']:
  if job['stage']!='benchmark':continue
  assert sha(job['tree'])==job['raw_sha256'];rows.append(dict(case=job['case'],tree_sha256=job['raw_sha256'],players=one(job['tree'])))
 result=dict(exploratory=True,rows=rows,median_required_fraction=statistics.median(p['fraction_required'] for r in rows for p in r['players']),source_sha256=sha(Path(__file__)),limits=['One saved profile per case; player 1 here has not seen a player-0 update','Weighted strategy averages still require correct accounting for untouched infosets','Finite underflow could remove extremely small reach, matching the existing traversal only with identical arithmetic','No sparse update algorithm, speedup or strength claim from counts'])
 with (OUT/'activity.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result))
if __name__=='__main__':main()
