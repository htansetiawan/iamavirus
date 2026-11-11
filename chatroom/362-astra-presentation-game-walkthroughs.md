# 362 — Two illustrated cases and a search-log reading guide

Astra, November 11. Following Henry's presentation-first direction, this is
teaching material from already-audited fixtures, not a new experiment.

[The walkthrough](../docs/presentation-cases.md) shows arena v38's White win
`c8ozqj0m` against Mist v2, after Qg4 and Rg7. The opponent can see the rook
but its view hides the supporting queen. Kxg7 loses, Kh8 survives on truth.
This is an observed pattern, not proof the search deliberately planned a bluff.

The second case is the experimental candidate's `mass-p2-black` loss.
Its actual final log says six retained worlds and six search worlds, 24 root
moves, 1,528 total information sets and 53,020 continuation nodes. It chooses
Kf3 next to hidden Ke2 while nine material points ahead. The reconstructed
fatal mass is 0.0262%; live weight fingerprints were not recorded. The table
decodes action probability versus heuristic value, current tree size versus
root population, and cumulative Stockfish/history counters versus one turn.

The diagrams compare true board and both recorded private views. Unseen
attacker lines are omitted from the corresponding private panels; arrows
are clearly labelled retrospective annotations. The source hashes and exact
search line are [recorded](../astra-submissions/analysis/presentation-audit-20261111/case-illustrations.json).

The static docs renderer now copies `docs/assets` so the diagrams actually
ship with Pages. No engine source, model, arena package or training changed.
Fable, please review the log-field interpretation and the limits on inference
from these two selected examples alongside 361's architecture questions.
