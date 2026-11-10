"""Clock-checked original adapter with an explicit deployment population cap."""
import importlib.util
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[1]/'guard-opponent-clock-20261109/checked_adapter.py'
spec = importlib.util.spec_from_file_location('bounded_misty_adapter', SOURCE)
checked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checked)


class BoundedProfile:
    def __init__(self, profile):
        self.profile = profile

    def build_strategy(self, **kwargs):
        kwargs['p_max_size'] = 200000
        directory = os.environ.get('ASTRA_MISTY_TELEMETRY_DIR')
        if directory:
            kwargs['capture_telemetry'] = True
        strategy = self.profile.build_strategy(**kwargs)
        if strategy._p_max_size != 200000:
            raise RuntimeError('Misty deployment cap was not applied')
        if directory:
            path = Path(directory)/f'misty-{os.getpid()}.jsonl'
            if path.exists():
                raise RuntimeError('Do not overwrite an existing telemetry trace')
            strategy.set_telemetry_sink(str(path))
        print('misty-cap: states=200000', file=sys.stderr, flush=True)
        return strategy


checked.adapter.PROFILES = {name: BoundedProfile(profile) for name, profile in checked.adapter.PROFILES.items()}

if __name__ == '__main__':
    checked.adapter.main()
