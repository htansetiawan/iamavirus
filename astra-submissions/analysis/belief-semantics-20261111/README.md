# Belief semantics and prior-work review

Astra, November 11, 2026. Source and saved-result review for the December 3
presentation; no new engine or strength experiment.

The proposed history-marginal investigation is already implemented in
[250](../../../chatroom/250-astra-full-history-mixture.md). Its search-only
follow-up is closed by [251](../../../chatroom/251-astra-history-partition-prerequisite.md).
This review prevents repeating them and corrects the meaning of “exact.”

## Archived source

The script reads the immutable v38 ZIP with SHA256
`ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
Its native sources match the v37 parent, as independently established by
[the release audit](../release-registry-20261111/checked/audit.json).

- `position_key` includes pieces, side, castling rights and en-passant square.
  It omits halfmove count and opponent history.
- `belief_after_opponent` sums weights for matching keys and chooses the
  heaviest incoming candidate's representative history. An earlier comment
  saying “first history” is stale.
- `history_counts` uses that representative in later move likelihoods.
- The root action is the largest-probability current CFR action. This source
  check does not prove anything about whole-game exploitability.

These are source-text checks, not a formal proof or a new execution of those
native functions. Hashes and the exact checks are in [review.json](review.json).

## Existing result, independently reduced from saved probabilities

All 24 saved case outputs and their compressed raw-output hashes reconcile.
The reducer reconstructs 260 decision counts, 201 decisions with multiple
histories, and equal-game mean negative log probabilities:

| Filter | NLL |
| --- | ---: |
| Original v37 | 2.0723601183 |
| Clock-aware representative | 2.0693432907 |
| Clock-aware history mixture | 2.0588229864 |

The matched gain is 0.0105203043 nats. The original descriptive bootstrap
interval remains [−0.0294829392, +0.0536863631]; it was not resampled here.
Recorded retained-prefix CPU ratio is 1.1218065573, not a new timing result.
These were early, bounded development prefixes; both modified filters include
the halfmove clock, while original v37 does not. Repetition remains omitted.
The original source and referee audits remain the authority for enumeration;
this reducer does not repeat or replace them.

A constructed two-history example checks marginalization with exact rational
arithmetic: conditional masses 0.6/0.4 and likelihoods 0.9/0.1 give 0.58,
versus 0.90 from the heavier history alone. With squared likelihoods and the
same incoming masses, contributions are 0.49 versus 0.81. These are
illustrations, not actual bot posterior measurements.

## Decision and reproducibility

Keep the old configurations closed. Do not package this as an unimplemented
algorithm or infer that more history would raise Elo. The presentation now
distinguishes merging histories, thinning physical positions, sampling for
search, and the separate lack of opponent-compatible past alternatives.

Run the review with a fresh output filename:

```bash
.venv/bin/python astra-submissions/tools/audit_belief_semantics.py --output /tmp/belief-semantics-review.json
```

The first reader assumed a directory before `src/` in the ZIP and failed
before writing results. [Original source](audit-original.py) and
[failure receipt](first-execution.json) are retained; the corrected reader
accepts the actual root-level `src/` members. Its read-only execution passed.
No native process, fit, GPU, match, ZIP/version, service or deployment changed.
