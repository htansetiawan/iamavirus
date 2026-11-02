from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/posterior-capacity-20261102'
PREVIOUS=HERE.parent/'posterior-fit-20261102'
sys.path.insert(0,str(PREVIOUS))
import extract as exporter
exporter.OUT=OUT
from model import Dataset, logsum
_spec=importlib.util.spec_from_file_location('fit231_runner',PREVIOUS/'run.py')
_runner=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_runner)
baseline_parity=_runner.baseline_parity
game_mean=_runner.game_mean


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unique(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
