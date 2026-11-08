"""Exercise packaged fallback with absent and startup-failing scorer copies."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

from validate_zip import HERE, OUT, DEST, STAGED, clean_env, referee, sha, write
from local_turn_control import group_members


def main():
    os.sched_setaffinity(0, {2,3})
    os.environ.clear(); os.environ.update(clean_env_saved)
    manifest = json.loads((OUT/'staged.json').read_text())
    validated = json.loads((OUT/'zip-validation.json').read_text())
    assert sha(STAGED) == manifest['archive_sha256'] == validated['archive_sha256']
    assert sha(DEST/'mist') == validated['native_sha256']
    ref = referee(); rows = []
    root = HERE/'build/failure-probe'; root.mkdir(exist_ok=False)
    with zipfile.ZipFile(STAGED) as z:
        for mode in ('absent', 'startup_exit_127'):
            work = root/mode; work.mkdir()
            for member in ('run.sh','data/history.bin'):
                p = work/member; p.parent.mkdir(exist_ok=True, parents=True)
                p.write_bytes(z.read(member))
                assert sha(p) == manifest['source_sha256'][member]
            shutil.copy2(DEST/'mist', work/'mist')
            if mode == 'startup_exit_127':
                p = work/'bin/stockfish'; p.parent.mkdir()
                p.write_text('#!/bin/sh\nexit 127\n'); p.chmod(0o755)
            for side in (True,False):
                board = ref.FowBoard(); start = time.monotonic()
                bot = ref.Bot(['/bin/bash',str(work/'run.sh')],side,180,2,initialization_timeout=15)
                row = dict(mode=mode,side='white' if side else 'black',startup_seconds=time.monotonic()-start)
                try:
                    assert row['startup_seconds'] < 15
                    bot.observe(ref.observation(board,side),0)
                    if not side:
                        board.push_uci('d2d4');bot.observe(ref.observation(board,side),1)
                    move, elapsed = bot.move(2)
                    assert move in {m.uci() for m in ref.fow_moves(board)} and elapsed < 2
                    row.update(move=move, elapsed_seconds=elapsed)
                finally:
                    bot.close()
                    row.update(stderr=bot.stderr_excerpt.decode(),failure=bot.failure,
                               live_members=[r for r in group_members(bot.proc.pid) if r['state'] not in ('Z','X')])
                    rows.append(row)
                assert bot.failure is None and not row['live_members']
                assert 'mist: stockfish ready' not in row['stderr']
                if mode == 'startup_exit_127':
                    assert 'mist: stockfish failed to start; our evaluator scores the leaves' in row['stderr']
    write(OUT/'failure-probe.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,rows=rows,
        archive_sha256=sha(STAGED),native_sha256=sha(DEST/'mist'),script_sha256=sha(__file__),
        scope='Exact run.sh/history and previously validated native build; isolated copies omit or replace only the scorer. '
              'Two-second clock probes, both colors; resilience only, not playing strength or all runtime failure modes. '
              'Staged ZIP and timed-game bytes are untouched.'))
    print(json.dumps(dict(passed=True,calls=len(rows),max_startup=max(r['startup_seconds'] for r in rows))),flush=True)


clean_env_saved = clean_env()
if __name__ == '__main__':
    main()
