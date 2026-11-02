from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis/sparse-cfr-20261102/search'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def unique(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
