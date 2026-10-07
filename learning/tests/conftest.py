import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

KIT = Path(os.environ.get("FOW_KIT", Path.home() / "git" / "fow-starter"))


@pytest.fixture(scope="session")
def referee():
    """The course referee module, when the kit and python-chess are available."""
    if not (KIT / "referee.py").exists():
        pytest.skip("set FOW_KIT to the extracted starter kit")
    pytest.importorskip("chess")
    sys.path.insert(0, str(KIT))
    import referee as module  # noqa: E402
    return module
