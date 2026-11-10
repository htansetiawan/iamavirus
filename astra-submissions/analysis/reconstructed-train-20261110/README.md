# Training states recovered without the drive or API

**4,000 original TRAIN games are reconstructed and independently verified.**
The working cache contains356,161 frames /352,161 actions in26,014,751bytes
(24.81MiB including index/manifest). The fixed records alone use22,794,304bytes.
This unblocks structural imitation/prior/representation data preparation while
the external drive remains unavailable. It does not restore the full raw
archive, actual clocks, recorded results or the fresh daily learning pipeline.

The original source/plan263610c36c7bf8ead1fe1f2e349a9dd98e22c806 was verified
on both mirrors before build. Original handle77887 completes with exit0.
Build:106.95seconds; independent read-only packed verification:72.30seconds.
Every state agrees with both the C engine and pinned course rules, including
board, both views, castling, EP, halfmove and side. Every action is legal and
the entire decoded trajectory matches its frozen source signature. No API,
GPU, model fit, new candidate or arena action. Cores2–3 are released.

| Curated action category | Count |
|---|---:|
| All actions |352161|
| Reference-team mover |233410|
| Original293 selected training examples |92940|
| Reference after eight own moves, native-surviving |190278|
| Above, quiet targets |145711|
| Above, capture targets |44567|
| Original-selected after eight moves, native-surviving |72338|

These are data-availability counts, not a new training selection or model
result. The original4000TRAIN split/order and selected indices are retained;
old validation/test and307 trajectories were not materialized or scored. The
source plan contains their metadata but only TRAIN traces enter this cache.
Repeated training data are not an independent test set.

The64-byte row format reuses011's existing32-byte nibble codec. Board plus
two visibility masks reconstructs both views without mistaking hidden for
empty. World castling/EP/halfmove, demonstrated action, selection and fatal
flags are privileged. Actor models must use the restricted projections and
causal windows; a raw privileged row is not an actor observation. The16
codec/privacy tests include hidden-cell and opponent/current-action mutation;
26 native/course special-move preflight frames also pass.

The cache has no clock/result defaults. It is derived state data, not original
raw replay bytes or a protocol/timing transcript. Complete-manifest loading
requires the data/index hashes; partial output is not accepted. The source
moves plus rules determine the recovered structural fields. Recovery does not
re-prove unavailable original JSON metadata or claim that the raw store works.

The temporary working directory is:

    data/astra-spool/reconstructed-train-20261110/

The shared raw/derived symlinks and actor-only SQLite index are untouched.
Storage remains below its64MiB bound; cold storage of record remains the
Seagate. The builder and hashes make this cache reproducible from the frozen
move traces; it depends on the local audited native producer named in plan.

For a permitted observation, with the repository as working directory:

```python
import sys
sys.path.insert(0, 'astra-submissions/tools')
from reconstructed_cache import Cache, actor_view, actor_context

c = Cache('data/astra-spool/reconstructed-train-20261110')
try:
    g = c.games[0]
    rows = [c.record(g['start'] + i) for i in range(g['records'])]
    observation = actor_view(rows[16], side=0)
    context = actor_context(rows, side=0, target=16)
    assert context['clocks'] is None
finally:
    c.close()
```

Use `actor_events` for a linear recurrent pass through a game rather than
rebuilding every prefix. Row access after checksum loading is O(1); there is
no measured neural-training speedup claim. A future learned representation
must still earn its own predictive, posterior, native-cost and playing gates.
No closed teacher/student/prior experiment is reopened by this recovery.
