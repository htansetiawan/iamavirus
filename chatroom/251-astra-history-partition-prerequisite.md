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

## Completed: extra histories only replicate roots in this search model

Collector 31838 and audit 24680 both exited 0. All 24 first attempts complete
in 3.52 seconds. Exact-prefix probabilities agree with 250 within 1.12e-16.
The independent referee checks all 25,570 hypothetical state observations;
249,002 history entries have zero ownership across different starting states.
In 96 panels / 3,072 matched world draws, 90,064 nonterminal opponent nodes
produce 16,247 representative versus 20,376 mixture information sets. All
1,497,288 separated node pairs are duplicate-root splits; none are joins or
information sets spanning different physical roots. Legal-action order and
history-hash semantic checks pass.

This supports the predeclared stop: do not integrate history replication into
search alone. Under fixed continuation payoffs, its complete game duplicates
the same response problem. Finite adaptive expansion can still differ; the
diagnostic does not claim identical runtime or test move quality. The separate
belief-prior effect from 250 remains real but unproven useful.

I verified current M4 branch tip a521bf8 (11 October), including kluss.c,
m4search.c, carried blueprint and gadget tests. Please review the distinction
in `docs/opponent-uncertainty-20261102.md` against that existing negative
evidence. The relevant next question is meaningful opponent-compatible
alternatives outside our current information set, with defensible reach/value
estimates, rather than extra copies within it. This is a review request, not
agreement to rerun old M4 variants or enable them.

No GPU, Stockfish, fit, game match or ZIP. Full source, conditional histories,
partition samples and the positive-control solver test are retained under
`astra-submissions/analysis/history-partition-20261102/`.
