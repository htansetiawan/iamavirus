from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/posterior-fit-20261102'
PREVIOUS = HERE.parent / 'posterior-objective-20261102'
sys.path.insert(0, str(PREVIOUS))
from common import array, encode, library, position_tuple, StateKey
sys.path.insert(0, str(ROOT))


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
