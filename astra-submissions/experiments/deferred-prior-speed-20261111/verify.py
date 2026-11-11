"""Audit exact trajectory parity and incremental timing from raw outputs."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'large-regime-exact-speed-20261110'))
from audit import audit


if __name__=='__main__':
    audit(HERE.name,('original','eager','combined'),10788,'2f11259524e8e391ce546d807da9ee5ebea9d886',
          'exact_deferred_full_clock_design_allowed','close_exact_deferred_speed_gate')
