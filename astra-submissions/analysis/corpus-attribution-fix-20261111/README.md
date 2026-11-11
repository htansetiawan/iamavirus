# Isolated fix: an unnamed corpus seat is unknown

The move-list corpus does not identify its selected player. The current
importer invents IAmAVirus and treats names as player IDs. Verified API recovery
finds this attribution false in 136 of its 164 games.

The [patch](ingest-attribution.patch) uses `Unknown corpus seat`, records the
selected color as `corpusSeat`, and leaves both unavailable player IDs null.
It retains the known opponent name. Moves, observations, outcomes and the
importer's existing immutable-cache behavior stay identical.

The [test](../../tools/test_corpus_attribution_fix.py) stages a copy under
`astra-submissions/experiments/corpus-attribution-fix-20261111/ingest.py`.
It imports two real source games, one selected white seat and one black,
through both original and staged code. Both are accepted; all 197 frames and
every other replay field agree. The old wrong label is reproduced, and the
patched copy invents neither team nor player IDs. Running the staged importer
against the existing test cache skips both entries and preserves all bytes.

[Result](result.json) records source, patch and native-validator hashes.
The validator is an existing pinned C++ rules library; no playing engine or
source rebuild ran. The patch SHA-256 is
`5c7423ff1f8fe6b67fb0e9662a62628c3c5fdd9c1c8a969980aa14ff9f704598`.

**Staged for Fable review; shared `learning/ingest.py` is unchanged.** Applying
this patch prevents future guesses. The separately verified metadata sidecar
provides historical corrections; old raw records and generations remain
immutable. No training, new split, model, game, Git publication or deployment.
