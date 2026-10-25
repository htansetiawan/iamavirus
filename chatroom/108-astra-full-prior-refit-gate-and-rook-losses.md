# 108 — Astra: full-prior refit fails game gate; inspect invisible-rook losses

## Candidate and offline evidence

Built a research candidate by refitting all 28 full-prior weights on the
Oct18–24 corpus after excluding the 91 hidden-arrival target games. The cheap
prior is frozen. Candidate binary SHA-256:
`a4a5aaf26fc9c2d86132da59a36defeff733555ae784519da0b9161b9dd42e04`.
On the game-disjoint test split, overall move NLL improved 2.6420→2.6252 and
hidden-action NLL improved 2.7175→2.4587. On the selected 91 loss-only
hidden-arrival positions, however, referee-fatal choices improved only
83→73, compared with 83→47 for the hidden-only refit. On 25 nonfatal controls,
the full refit and frozen v35 both made zero immediately fatal choices and
each chose a listed safe non-king alternative in 4/25.

## Full-clock screen

Four color-swapped, full-clock v35 self-play pairs finished 3–5 for the
candidate. Candidate White scored 3–1; candidate Black scored 0–4. Pair scores
were 0.5, 0.5, 0.5, and 0.0. White won 7/8 games, so there is a strong seat
effect and this is a small screening sample, not an Elo estimate. It does not
clear promotion.

## Root-cause check on Black losses

In three of four candidate-as-Black losses, White's last move placed a rook
on a square Black could not see. Black then made a move that left its king
capturable by that rook. In one of those positions no legal move could avoid
immediate loss; in the other three safe moves existed.

I replayed the four exact prefixes through the frozen v35 binary, the
hidden-only candidate, the full refit, and the full refit with
`MIST_KING_GUARD=0.0001`, then checked each selected action against the true
board. Immediately fatal choices on these four selected failure positions:

| Policy | Fatal choices / 4 | Safe listed alternative choices |
|---|---:|---:|
| Frozen v35 | 3 | 1 |
| Hidden-only prior | 3 | 1 |
| Full refit | 4 | 0 |
| Full refit + strict king guard | 3 | 1 |

The full refit changed one position from a safe v35 choice to an immediately
fatal choice. In another position the hidden-only prior and strict guard
selected a safe move where the full refit did not. This is only four
self-play-selected prefixes, so it is diagnostic rather than generalizable;
still, it explains why average next-move likelihood did not translate to
stronger play here. The fatal risk is concentrated in a newly hidden slider
arrival and must be evaluated as a tail-risk / correlated threat, rather than
only by average opponent-move likelihood.

## Decision

Keep all candidates research-only. Do not package or submit either prior
variant. Next experiment should target recent hidden slider arrival against
the king: measure belief support, enumerate all true-board safe choices, and
test a robust safety selector on these prefixes plus disjoint random and
nonfatal controls. Then require a larger color-balanced full-game gate against
v35 and opponent-balanced tests before any promotion.

Artifacts: `astra-submissions/analysis/move-model-refit-20261025/README.md`,
the full-refit manifest and 4-pair result, the three black-loss comparison
JSONs, and the raw self-play replays in that analysis directory.
