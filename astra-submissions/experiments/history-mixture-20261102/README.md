# 250: preserve opponent histories without duplicating physical boards

This is a native representation and diagnostic experiment. It does not change
the playing engine. Previous experiment 201 retained short move contexts,
omitted the empirical history table and did not integrate search information
sets. Here each retained board carries the mass of every distinct opponent
observation/action-history hash. This addresses the limitation documented in
note 163; it is not a newly discovered bug or full common-knowledge solving.

Use immutable v37 rules, fitted move likelihood and empirical history table.
Compare three filters on the same permitted replay prefix: original v37;
board/rule-state groups with one representative history; and identical groups
with all history masses. The latter two include halfmove clock in the grouping
key, so the representative control isolates history retention from that
separate change. These states still omit repetition history. The original
production key also omits halfmove clock; score board/side/castling/EP marginals
for a common comparison, reporting full-state matching separately.

For an opponent move, score static features once per physical parent, apply
the same history-table blend separately for each history, temper each
transition at the existing temperature, then merge matching (state, history)
successors by log-sum-exp. For our move, advance the board and append only the
opponent's resulting observation to its history. No opponent action is fed
from truth. Independent small-state enumeration and table-disabled parity are
required before replay diagnostics.

Stop prefixes at 4,096 physical states, 131,072 history entries, 64 plies,
or a native generation bound of one million candidates. Do not cap, thin,
rebuild or retry to make this experiment pass. These early/small prefixes do
not represent capped middlegames. Per-game subprocess limit 60 seconds; total
diagnostic limit 15 minutes. CPU0–1 only; no GPU or model fitting.

Select 24 existing v37 games after 05:28 UTC on 2 November, twelve per colour,
against the fixed nine reference opponents. Deduplicate complete move sequences
before salted ID selection; no outcome/label selection. This is reused public
development data, not a fresh playing-strength test. Freeze IDs before scoring.

Report history multiplicity, the probability mass outside the heaviest
history, history-table hit rates, board-marginal NLL and support, and CPU/memory
cost on common prefixes. No arbitrary redistribution of posterior mass or
promotion threshold is introduced here. A future integration needs a concrete
effect on predictions or information-set grouping, acceptable resource cost,
and separate decision/match tests. Keeping histories alone does not implement
Obscuro's knowledge-limited subgame or resolving machinery.

Reference: [Obscuro, Appendix B.1](https://arxiv.org/html/2506.01242v2#A2.SS1)
distinguishes physical states from players' observation/action sequences and
information sets. Our finite hash representation is an approximation, with
collision and state-abstraction limits retained explicitly.
