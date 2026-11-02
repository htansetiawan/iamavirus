from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/residual-fow-value-20261102'
OLD = HERE.parent / 'native-fow-value-20261102'
QUERY = HERE.parent / 'query-fow-value-20261102'
OLDOUT = OUT.parent / 'native-fow-value-20261102'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_new(p, d):
    with Path(p).open('x') as f:
        json.dump(d, f, indent=2, allow_nan=False); f.write('\n')
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
