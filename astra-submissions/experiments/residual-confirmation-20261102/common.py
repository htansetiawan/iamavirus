from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/residual-confirmation-20261102'
OLD = HERE.parent / 'native-fow-value-20261102'
OLDOUT = OUT.parent / 'native-fow-value-20261102'
QUERY = HERE.parent / 'query-fow-value-20261102'
QUERYOUT = OUT.parent / 'query-fow-value-20261102'
RESIDUAL = HERE.parent / 'residual-fow-value-20261102'
RESIDUALOUT = OUT.parent / 'residual-fow-value-20261102'
REFRESH = OUT.parent / 'arena-refresh-20261102-residual'

def now(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def sha(p): return digest(Path(p).read_bytes())
def write_new(p, d):
    with Path(p).open('x') as f:
        json.dump(d, f, indent=2, allow_nan=False); f.write('\n')
