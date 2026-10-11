# 068 — Astra: cap support loss and protected bait are separate failures

The read-only trace matches all 1,680 original non-timing outputs. All 21 first
true-board support losses in the cap-10,000 development cohort occur during cap
selection, after correct expansion/filtering. Nine lost states rank in the top
10,000. This is one fixed cap and seed, not live-cap or Elo evidence.

The fresh Instructors bait `4bkwxxng` has a different cause. Our experimental C
replica retains the true board among only 59 states. It still chooses Kf8xe7
when searching all 59 roots at one and four seconds with Stockfish verified
ready. Kg8 is immediately safe in all retained states, but its continuation
value is estimated worse. Independent referee reconstruction checks 5,991
hypothetical tree nodes. Surviving Kg8 does not prove the position is winning.

The initial Stockfish probe actually fell back to the internal evaluator; it is
excluded. I added a fail-fast check, verified with `/bin/false`, to prevent that
arm confusion. Six more public games (2W–4L), 467 frames, are independently
validated. No bot release or default changed; the completed CPU lease is freed.

Evidence: `astra-submissions/analysis/m4-support-loss-20261011/README.md` and
its inventory, raw traces, source, comparison reports and public replays.

Next concrete test: the existing weighted-without-replacement cap keeps original
weights after weight-biased selection. Test finite-state resampling with known
inclusion probabilities and corrected retained weights in an isolated copy.
Keep large weights, sample the remainder, and compare sequential support **and**
risk calibration. This must not be silently merged into your shared belief code.
