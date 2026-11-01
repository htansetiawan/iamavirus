#!/usr/bin/env python3
"""Export the frozen fits; no optimization or new model selection."""
import argparse, hashlib, json
from pathlib import Path

def literal(x):
    s=format(x,'.9g')
    return (s if '.' in s or 'e' in s else s+'.0')+'f'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('fit',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    manifest=json.loads((a.fit/'frozen-models.json').read_text())
    text=['/* Frozen supervised fits. Order: 39 static, 52 temporal, 384 from, 384 to. */','#ifndef ASTRA_TEMPORAL_LEARNED_H','#define ASTRA_TEMPORAL_LEARNED_H']
    for name in ['static','temporal']:
        p=a.fit/(name+'.json');assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['models'][name]['sha256']
        c=json.loads(p.read_text())['coefficients'];assert len(c)==859
        text.append(f'static const float learned_{name}[859] = {{')
        for i in range(0,len(c),8):text.append('  '+', '.join(literal(v) for v in c[i:i+8])+',')
        text.append('};')
    text.append('#endif');a.out.write_text('\n'.join(text)+'\n')
    print(json.dumps({'header_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'parameters_per_model':859,'float32_bytes_per_model':3436}))
if __name__=='__main__':main()
