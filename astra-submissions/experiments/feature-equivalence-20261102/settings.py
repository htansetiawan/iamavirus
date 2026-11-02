from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/feature-equivalence-20261102'
PREVIOUS=HERE.parent/'posterior-fit-20261102'
sys.path.insert(0,str(PREVIOUS))
from config import array,encode,library,position_tuple,StateKey


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unique(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
