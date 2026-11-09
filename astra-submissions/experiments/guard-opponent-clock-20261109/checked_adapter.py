"""Original observation-only adapter plus a fail-fast clock-configuration guard."""
import importlib.util
from pathlib import Path
import sys

ORIGINAL = Path(__file__).resolve().parents[1]/'obscuro-fidelity-20261108/misty_adapter.py'
spec = importlib.util.spec_from_file_location('clock_checked_misty', ORIGINAL)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class CheckedProfile:
    def __init__(self, profile):
        self.profile = profile

    def build_strategy(self, **kwargs):
        strategy = self.profile.build_strategy(**kwargs)
        if not strategy._clock_time_enabled or strategy._time_budget is not None:
            raise RuntimeError('Misty gate requires its clock manager ON and no fixed budget')
        budget = strategy._time_manager.budget_for(180000, 2000, static_fallback_s=None)
        if budget is None or not 0 < budget <= 10:
            raise RuntimeError('Misty initial clock budget is missing or outside the expected cap')
        print(f'misty-clock: enabled=1 fixed=none budget180={budget:.3f}', file=sys.stderr, flush=True)
        return strategy


adapter.PROFILES = {name: CheckedProfile(profile) for name, profile in adapter.PROFILES.items()}

if __name__ == '__main__':
    adapter.main()
