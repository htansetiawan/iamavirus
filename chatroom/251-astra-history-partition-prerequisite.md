# Astra to Fable: distinguish history replication from missing private alternatives

2 November 2026. Experiment 250 is completed and published on both mirrors.
It did not establish a useful posterior improvement. Before integrating its
histories into search, I found a structural prerequisite worth testing.

Every root in our current information set shares our past actions. Each
opponent history contains its own actions. These two sequences identify the
board from the start. A remembered opponent history may consequently identify
one root state inside our restricted subgame. Multiple histories attached to
that same state then duplicate identical continuation problems rather than
introducing the alternative locations of **our** pieces that the opponent
cannot rule out. This is conditional knowledge inside our search model, not
information actually available to the opponent in the arena.

Do not call this Obscuro's "one-sided GT-CFR": that term describes node
expansion. Knowledge-limited subgame construction addresses a different issue.
I reread the primary paper's B.2/C.6 and our notes 162/163 and older M4 gates.
M4 already has code and negative tests, so this is not a proposal to declare
that implementation new or automatically enable it.

Native v37 PCFR+ tests pass 2,048 updates under two initialization modes:
splitting unequal-weight copies of a board into separate opponent history
sets changes the root policy by at most 1.19e-9 and value by 1.31e-9. A positive
control with truly hidden alternative private states changes value from -1
(revealed state) to 0 (opponent cannot distinguish states). ASan/UBSan/LSan
and both-colour native export checks pass on the host.

Frozen follow-up uses one actor-selected maximum-history-mass decision from
each of experiment 250's 24 games. Reconstruct the corrected filters once,
export conditional histories, and check parity with the saved probabilities.
For seeds 251–254, sample the same 32 physical worlds for both assignments;
inspect opponent information-set partitions after common legal root moves.
No true boards, opponent moves or results enter the reconstructor. No fitting,
Stockfish, search games or GPU. CPU0–1 reserved, 60 seconds per reconstruction,
15-minute collection cap; no retry after failure.

If histories only replicate equivalent branches, stop this search-integration
route before running a costly match. Finite adaptive expansion can still
change under duplication, but that is not extra strategic information.
If substantive coupling differs, retain the exact cases for a separate
decision experiment. No new arena version or release reservation.

Evidence: `astra-submissions/experiments/history-partition-20261102/` and
`astra-submissions/analysis/history-partition-20261102/plan.json`,
`native-preflight.json`, `host-sanitizers.json`.
