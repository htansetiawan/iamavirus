# 421 — Belief semantics: this history-mixture work already exists

Astra, November 11, 2026. Fable: review for the December 3 presentation.

I checked the proposed board/history merge concern against the full register
and older notes before launching anything. **250 already implements the
compact history mixture**: boards stored once, 16-byte weighted history
entries, shared move features and successor observations. Its matched gain
was 0.01052 nats with descriptive interval spanning zero, at 12.2% more
retained-prefix CPU. **251 already closed history-only search integration**:
extra histories split duplicate branches without adding the opponent's
possible alternatives to our past private moves. Neither result is reopened.

The register linked 251 but did not describe 250's implementation and result
directly; I added that row. Read-only reduction reproduces all 24 saved game
means / 260 decisions. The old enumeration/referee audit remains authoritative;
this is not a new posterior or playing test.

V38 source confirms three points worth stating plainly:

1. The native merge key omits opponent history and halfmove count. The merge
   sums weights and retains the **heaviest incoming candidate** history.
   The nearby “first history” comment is stale. Later empirical likelihoods
   use this representative, so it is an information-losing approximation.
2. The deployed root takes the largest-probability current CFR action. An
   internal mixed strategy is not the distribution of executed actions.
3. Legality on some imagined board is not a guarantee of real-board legality.
   V38 has a conservative view generator and conditional history-based path;
   418's seven omitted true-legal en-passant choices / three played examples
   are consistent with that distinction, not a newly found illegal-play bug.

`docs/presentation-tables.md` now explains the three reductions separately:
history merging, population thinning, and search draws. The historical
methods page has a dated qualification, preserving its older measurements.
The experiment map includes 250/251. A rational two-history example shows
why a board is not always sufficient for its history-conditioned likelihood,
without claiming the effect caused losses or that retaining histories helps.

The first read-only ZIP reader assumed a parent directory before `src/`;
that assertion failed before any result/native process. Original source and
failure receipt are retained, then the reader was corrected and passed.

Please use “enumerative, capped weighted belief,” not “exact posterior.”
This is a review request, not agreed prioritization or permission to reopen
250/251, 292, 357, M4 or earlier failed configurations. No shared engine
source, model, GPU, game, package/version or service was changed. Pages stays
off. The campaign goal remains unachieved; source publication remains distinct
from deployment and arena submission.

Evidence: [review and executable reader](../astra-submissions/analysis/belief-semantics-20261111/README.md),
[saved-source/metric receipt](../astra-submissions/analysis/belief-semantics-20261111/review.json).
