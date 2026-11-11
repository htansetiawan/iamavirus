# 361 — Presentation understanding takes priority through December 3

Astra, November 11. Henry has changed the immediate priority. Producing v39
is less important than understanding the system for the December 3 final
presentation: what is implemented, what is absent, how the parts work, how
many tables there are, what we tried, and what the limitations are.

I will start no new candidate experiment or training run in this phase.
The 357 match is terminal and rejected at 1W–8L; its final independent audit
and 360's descriptive diagnosis are being recorded. The already running
bounded 359 public replay collection can finish into its isolated SSD cache.
It does not alter the arena bot or repair the shared daily pipeline.

The presentation audit uses the actual immutable v38 ZIP, not the current
mist-c checkout or the old v35 specification. Initial source inspection finds
that the deployed history file has **359,889 history/move records** across
**219,137 distinct 64-bit history keys**, rather than the old 151,316-record
figure. It is 5,758,240 bytes. There are two 28-coefficient move-model vectors.
The archived source says their refit used 148,357 games; that training count
is a source-recorded provenance claim, not a new independent fit audit.

Fable, please review these teaching points against the deployed archive:

- Belief rows, board merging and the representative opponent history.
- The empirical table versus fitted model coefficients versus transient CFR
  regrets; which survive a move and which survive a game.
- Exact terminal rules versus the approximate Stockfish frontier, including
  the v38 all-child scorer's numerical/strength tradeoff.
- The parts of Obscuro present in v38, absent from v38, and implemented only
  in the experimental M4 branch. Preserve M4's negative match evidence.
- The evidence chain from action prediction to posterior quality to whole
  games. The newly rejected 357 prior is a concrete counterexample to treating
  positive posterior scores as proof of stronger play.

I am preparing a short overview, a table/algorithm reference and an experiment
map in `docs/`, with a reproducible archive inventory under `astra-submissions/`.
The current presentation duration and deliverable requirements are awaiting
Henry's clarification. No new release number is reserved.

## First review packet delivered

- [Presentation brief and move lifecycle](../docs/presentation-20261203.md).
- [Table inventory, probability updates and PCFR+ equations](../docs/presentation-tables.md).
- [Curated experiment map and the prediction/posterior/strength distinction](../docs/presentation-experiments.md).
- [Archive inventory](../astra-submissions/analysis/presentation-audit-20261111/inventory.json):
  all 114 manifest member hashes checked, 115 ZIP members; history header,
  record sizes, unique history/move pairs and sorted keys verified.

Two additional source-level details for review: the generic `Game.strategy`
array is allocated but the deployed path computes strategies into separate
temporary buffers; and the outer FoW tree does not explicitly adjudicate
threefold/50-move draws. Stockfish receives the halfmove field, and the front
end discourages some repetitions, but those are different mechanisms. No
effect on a specific arena result is claimed. These are teaching/audit
findings, not newly authorized candidate changes.

The latest 357/360 audits are complete. The playing candidate closes 1–8,
901 frames, zero faults/thinnings/rebuilds. The six-path diagnosis improves
truth log share +0.61221 nats over 247 primary decisions yet includes four
improving losing paths. One terminal loss had six retained worlds, all
searched. This will be a central example of why positive inference scores
do not automatically imply better play.
