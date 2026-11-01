#!/usr/bin/env python3
"""Lossless compression; use `unpack` before run.py verify in a fresh checkout."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[2]/'astra-submissions/analysis/conditional-exchange-20261101'
mode=sys.argv[1];assert mode in ['pack','unpack']
for row in map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()):
    p=OUT/(row['name']+'.audit.json');z=p.with_suffix(p.suffix+'.gz')
    if mode=='pack':
        data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==row['audit_sha256']
        compressed=gzip.compress(data,compresslevel=6,mtime=0);assert gzip.decompress(compressed)==data
        z.write_bytes(compressed)
    else:
        data=gzip.decompress(z.read_bytes());assert hashlib.sha256(data).hexdigest()==row['audit_sha256']
        if p.exists():assert p.read_bytes()==data
        else:p.write_bytes(data)
print('Six audit files verified and',mode+'ed')
