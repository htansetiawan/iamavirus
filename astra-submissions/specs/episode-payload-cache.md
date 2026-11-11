# Incremental episode construction: isolated prototype

The existing move exporter (273) caches validated move strings; the training
feature cache stores arrays after episode JSON already exists. The 336 packed
replay cache is another representation. This prototype instead reuses exact
serialized actor/target episode payloads before feature expansion.

The normal exporter remains running and unchanged. The prototype is confined
to Astra and a small private SQLite file; it creates no published generation,
training model, engine candidate or arena number.

## Contract

A key contains the full replay-content SHA and an explicit pipeline
fingerprint. The caller must bind that fingerprint to rules, episode/label
code, native validator and serialization version. A hit selects a pinned
content snapshot; it does not prove that a mutable raw path still has those
bytes. Production use needs a trusted ingestion manifest carrying the content
hash, not an assumption based only on game ID or mtime.

Cache records preserve actor and target JSON bytes. Only small metadata is
reserialized for the requested fold, leaving the existing splitter and both
color assignments under the caller's control. Stored compressed and raw hashes,
bounded decompression, source-key checks and SQLite transactions detect
corruption or conflicting entries. An error stops the caller; no replay or
sample is silently omitted. Existing holdout provenance still matters.

## Bounded check before proposing integration

- Fixed inputs: all thirty already reviewed 389 games, plus the first two
  technical games with at least four plies in 379's frozen source journal.
- Exact decompressed JSON-line parity for both colors and all three folds.
- Check source/pipeline invalidation, malformed keys, source mismatch,
  corrupt compressed/raw payloads, interrupted builders and failed writes.
- One cold fill and six paired baseline/warm passes, order AB/BA alternating,
  core 6, 300-second total execution cap. Inputs are already pinned in memory;
  raw-directory reads, full gzip writing and full production scale are excluded.
- Necessary engineering gates: all correctness checks; median warm time at
  most half the paired baseline; cold fill at most twice baseline median.
  No tuning or repeated timed attempt after a failed result.

Passing earns a reviewed integration design, not a production switch. Reuse
can remove repeated reconstruction for old games, but emitting a full new
dataset still costs at least linear time in its output size. The small warm
probe cannot establish an end-to-end or full-corpus speedup, much less Elo.
