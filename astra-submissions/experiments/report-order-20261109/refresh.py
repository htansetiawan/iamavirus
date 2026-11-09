"""Reuse the bounded report collector in a new staging directory; no ingest."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
old=ROOT/'astra-submissions/experiments/report-repair-20261108/refresh.py'
spec=importlib.util.spec_from_file_location('bounded_report_refresh',old)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.OUT=ROOT/'astra-submissions/analysis/report-order-20261109'
module.STAGE=module.OUT/'reports'

if __name__=='__main__':module.main()
