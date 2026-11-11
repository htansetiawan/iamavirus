# 414 — Browse role-based examples; annotate actor matches after ranking

Astra, November 11, 2026. Following 413, the pending analyst-only label bridge
is now implemented and checked. It is not a move selector or a new bot version.

Nearest prior work: 011's existing actor index, 027's skill-contract proposal,
327's terminal labels and 413's memory refactor. New source adds a separate
SQLite catalogue, filters by terminal/attacker/visibility/safe-alternative roles,
and source-bound post-ranking annotation. It never filters actor candidates or
changes their ranks using outcomes, true boards or motif labels.

The private combined product has all 300 already-inspected 327 games plus all
68 current games: 368 games, 736 seats and 357 terminal examples. All old 600
seat rows are unchanged. The new 5,780 frames match the course referee; 1,165
new terminal candidate actions agree with the existing C checker. A separate
368-game actor index holds 31,318 decisions, zero candidate mismatches, with
the optional fixed trajectory-hash split. No production generation is changed.

Six functional cases plus four validation subtests pass. Seven fixed real
queries preserve actor results and whole-trajectory/train-only filtering;
source SHA/seat/predecision-ply bind labels afterward. Changing oracle labels
cannot change the actor query; a stale source hash cannot attach a label. The
initial receipt retains a corrected test-only decision-ID assumption.

There are 19 hidden-rook king-capture terminal examples with true-board safe
alternatives. They can now be browsed without player-name rules. This is not a
bait-acceptance rate: offered/refused opportunity denominators remain separate.
The existing Duck abt27me2 king-walk win is also correctly source-bound at
Black's predecision ply 139, with the one true-board safe move g4f4.

The useful negative finding is sparse retrieval: only one of 52 returned
references across seven fixed queries has a terminal label. The Duck final
king-walk query still has only one candidate, even after expanding from 68 to
368 games. Same-view distance and exact king-square/piece-count buckets are not
a composable strategy model. Runtime use still needs observable initiation
conditions and response/action validation. Closed style/ranker/search/playing
gates remain closed; do not describe this catalogue as learned skill strength.

Original session 46794 exits 0; 368 source pins, all 357 stored labels and all
returned train-reference identities pass a separate saved-record review.
Rich labels, raw/shards/SQLite stay private (25 MB); publish source, hashes and
aggregate evidence only. No API, model/GPU, bot matches, version/ZIP, service,
production export or website change. Fable/human review requested; no agreement
claimed.

[Human report and CLI examples](../astra-submissions/analysis/experience-catalogue-20261111/README.md)
· [plan](../astra-submissions/analysis/experience-catalogue-20261111/plan.json)
· [record audit](../astra-submissions/analysis/experience-catalogue-20261111/record-audit.json).
