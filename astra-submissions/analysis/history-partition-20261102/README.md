# History replication does not add the missing opponent uncertainty

**Do not integrate experiment 250's extra histories into search by themselves.**
The structural prerequisite test supports stopping before an expensive match.
This is a statement about the represented subgame, not a playing-strength
result or a claim that history never matters.

Experiment 251 selects one deliberately high-history-mass decision from each
of the same 24 development games. Its source and selection were committed as
`500c2bab738889a21a877538ed2a57d052b8232a` and verified on both mirrors before
collection. All 24 first attempts complete in 3.52 seconds; original handle
31838 exits 0. Analysis handle 24680 exits 0. No Stockfish, GPU, fitting or game
search is used.

## Evidence

| Check | Result |
|---|---:|
| Physical states reconstructed | 25,570 |
| Conditional history entries | 249,002 |
| Histories assigned to different starting states | 0 |
| Representative histories assigned to different starting states | 0 |
| Largest discrepancy from experiment 250's saved normalized probabilities | 1.12e-16 |
| Same-world sample comparisons: 24 cases × 4 seeds × 32 draws | 96 panels / 3,072 world draws |
| Nonterminal opponent nodes after common legal root moves | 90,064 |
| Opponent information sets, representative → mixture | 16,247 → 20,376 |
| Information sets spanning distinct starting physical states, either arm | 0 |
| Node pairs separated / joined by the new histories | 1,497,288 / 0 |

Counts pool cases and seeds; they are not independent population samples.
The 176 terminal branches are excluded from opponent information-set counts.
All reconstructed hypothetical states match the course referee's current
player observation and an independent state hash. Common legal root moves
come from the full reconstructed support. Next observations and action-order
consistency are checked with the course referee. These roots are not filtered
through the deployed king/queen guards.

The extra information sets only split equivalent copies of a starting state.
They preserve that state's action-to-next-observation partition. Different
root moves can still be indistinguishable to the opponent inside each copy;
this is not a claim that the entire search is perfect-information minimax.

## Why the restricted game has this property

Our current information set fixes our past moves. The opponent's full history
contains its past moves. Given the starting position, the two action sequences
determine the physical state. Thus the opponent history identifies a root
inside this restricted set, even though the opponent does not know our past
hidden moves in the real game. Extra histories for one state duplicate
continuation games; they do not add alternative hidden placements of our
pieces that lie outside our current information set.

For fixed physical-root weights and a fixed complete continuation game with
history-independent payoffs, duplicate histories do not change the minimax
objective. For any fixed strategy x of ours and state s, each history h is an
independent copy of the same opponent-response problem:

    min_{y_h} sum_h q(h|s) U_s(x, y_h) = min_y U_s(x, y),  sum_h q(h|s) = 1.

The equality requires that opponent information sets do not connect distinct
root states and that the copies have identical future policy constraints and
payoffs. The sampled partition checks establish the relevant initial
structure here; the native tests exercise that equivalence on controlled trees.

On immutable v37 PCFR+, five unequal-weight copies of two worlds, hidden
root-action pairs, two initialization modes and 2,048 updates yield maximum
root-strategy difference **1.19e-9** and value difference **1.31e-9**. In a
separate hiding-game positive control, actually coupling two different
private states through the opponent's information set changes value from
**−1 to 0**. The test can distinguish extra private alternatives from mere
copies. Host ASan/UBSan/LSan passes all three runs, including both-colour export.

## Limits and next decision

Experiment 250 separately showed that histories can change the empirical
**belief prior**. That effect is not being denied or mixed into this fixed-world
search question. The current search does not condition its continuation
opponent policy or leaf payoff on a learned history model.

Current position-based search omits repetition history. If a future evaluator,
opponent policy, clock state or repetition logic makes otherwise identical
boards history-dependent, the duplication argument must be revisited. Adaptive
tree expansion, visits, initialization and floating-point effects can also
change a finite GT-CFR run even when its complete game is equivalent. We did
not run actual search moves or claim identical full-runtime behavior.

The appropriate architectural question is whether a subgame includes legal
histories outside our own information set that the opponent cannot distinguish,
with defensible counterfactual weights and a carried strategy. This is related
to the paper's knowledge-limited subgame construction, not its separately
named one-sided GT-CFR expansion rule. See the [primary paper, B.2/C.6](https://arxiv.org/html/2506.01242v2).

Our existing `astra/m4` branch already contains that machinery. Its current
tip is `a521bf8c14a1253c3effc87dae15e55de47b4e13` (11 October), including
`kluss.c`, `m4search.c`, gadget and carry tests. Earlier tests were negative;
this result does not justify enabling it or rerunning the same failed variants.
Review whether those tests included strategically relevant private alternatives
and adequate counterfactual weighting before proposing a distinct experiment.

Raw conditional histories, frozen inputs, hashes, partition samples and
diagnostics remain in this directory. No production code, guard, release
number or arena ZIP changes. The broader improvement campaign remains open.
