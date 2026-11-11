# Inside v38: tables, probabilities and regret

*Companion to the [December 3 review](presentation-20261203.html).
Counts come from the immutable v38 archive audit, November 11 UTC.*

[TOC]

## How many tables do we actually have?

**One shipped empirical history lookup file, two fitted coefficient vectors,
and four persistent-within-a-decision CFR arrays.** The belief, search tree
and indexes are additional runtime structures. They have different keys,
sizes and lifetimes. There is no single giant learned table that contains
the whole strategy.

| Structure | Key and contents | Verified size or configured bound | Lifetime |
| --- | --- | --- | --- |
| Empirical history table, `history.bin` | Opponent history hash + encoded move → observed count | **359,889 rows**, **219,137 distinct 64-bit history keys**, **5,758,240 bytes**; summed recorded counts 2,200,230 | Frozen in package; loaded once per bot process |
| Full move-model vector | 28 move features → logit | **28 coefficients**, 25 nonzero | Frozen in package |
| Cheap move-model vector | Same 28 slots; costly features omitted | **28 coefficients**, 17 nonzero | Frozen in package |
| Belief rows | Complete position + representative opponent history + log weight | Up to **200,000** retained entries by default; can be smaller | Across turns within one game |
| Belief membership index | 64-bit position key → membership | Open-addressing hash table; grows with retained entries | Rebuilt/updated with the belief |
| Search nodes and edges | Chance/player/frontier nodes, action edges and chance probabilities | Variable; configured node limit **1,500,000** | One move |
| Information-set index | Acting player + represented history/action signature → information-set ID | Open-addressing map, variable | One move |
| Four CFR arrays | `(information-set ID, action)` → regret, previous instantaneous regret, allocated generic strategy field, accumulated strategy sum | **Four allocated arrays**; each has one slot per information-set/action pair | One move |
| Expansion visits and frontier records | Action visits; leaf board/history; node → leaf index | Variable with the tree | One move |
| Front-end repetition record | Our piece configurations and visit counts | Capacity **1,024 configurations** | Across turns within one game |
| Fixed move geometry | Square → knight/king attack bitboard | Two arrays of **64** entries | Initialized once; unchanged during play |
| Zobrist hash keys | Piece/square, side, castling-rook square and en-passant square → hash contribution | **897** 64-bit keys | Initialized once; unchanged during play |

The history record is 16 bytes: an 8-byte hash, 4-byte move and 4-byte count.
The file also has a 16-byte header. Distinct hashes are not a count of games
or a collision-free count of full histories. They are the lookup keys actually
stored. Stockfish has its own NNUE parameters, search history and transposition
table; those belong to the external evaluator, outside the four CFR arrays.

One implementation detail matters: the generic `strategy` field is allocated
and resized, but current strategies on the deployed path are calculated into
separate temporary buffers. It is not an additional learned model. Similarly,
the accumulated average is maintained although final action selection uses
the current iterate. Our last-only optimization experiments examined part of
this accounting; they are not deployed in v38.

**Reproducible count:**

```bash
.venv/bin/python astra-submissions/tools/audit_v38_presentation.py
```

[Audit source](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/tools/audit_v38_presentation.py)
· [Frozen inventory and source hashes](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/presentation-audit-20261111/inventory.json).

## How a hidden move changes the belief

For a hypothetical complete board `s`, the fitted model computes one logit
per possible opponent move:

```text
logit(s, a) = sum over 28 features of coefficient[k] × feature[k](s, a)
p_model(a | s) = exp(logit(s, a)) / sum over legal moves b exp(logit(s, b))
```

The full feature computation is selected for smaller populations, with a
default full-model threshold of 10,000; larger updates use the cheap model.
The feature vectors include captures, piece type, development, retreat,
recapture and, in the full model, attack relationships. The deployed vectors
give zero coefficients to the two explicit unseen-threat feature slots.
Those features and failed attempts to use them are already documented; they
are not a newly discovered untried improvement.

For a history seen enough times, empirical counts blend with the model:

```text
p_blend(a | s, h) = (count(h, a) + 4 × p_model(a | s)) / (N(h) + 4)
```

The default minimum history count is 3. Unseen/insufficient histories fall
back to the fitted model. The lookup first binary-searches the sorted history
hashes, then scans that history's move records. It is not a player-name lookup
or an exact solution lookup.

For every observation-compatible successor, the native default update adds
`2 × log(p_blend)` to its parent's log weight. This temperature sharpens move
likelihoods. Duplicate positions add their incoming weights; one opponent
history represents the merged board. Consequently, the implementation is
not a lossless distribution over every possible private history, and the
sharpened weights should not be called a guaranteed calibrated posterior.

The source comment records a refit on 148,357 arena games. Our audit verifies
the archived coefficients and their counts; it does not independently
reconstruct that historical training job.

## What do “32 weighted samples” mean?

Let retained board probabilities be `p[1] ... p[N]`. For `N > 32`, build their
cumulative weights and draw 32 independent random numbers against that
distribution. Binary search finds each selected board. Duplicate draws merge;
their search chance weight is their draw count divided by 32. For `N <= 32`,
include all boards with normalized retained weights.

These are plausible worlds, not the 32 worlds where we are winning most.
A world with probability 10% is ten times as likely to be drawn as one with
1%. A danger of total mass 1% is present in a 32-draw sample with probability
`1 − 0.99^32`, approximately **27.5%**. Thus it is usually absent from search.
The root guards examine more retained worlds, but remain limited by their
weighting, stride and definitions of danger.

Three different numbers must stay separate:

- Retained worlds: at most 200,000 by default, representing current uncertainty.
- Search draws: normally 32 with Stockfish, often fewer distinct root worlds.
- Search nodes: future move continuations, with a configured 1.5-million limit.

## What Stockfish is being asked

At a frontier position, Stockfish sees **both sides' pieces on one imagined
complete board**. It scores candidate children with a short depth-1 search,
which can include tactical continuation work rather than a single static
network call. NNUE supplies conventional chess evaluation within Stockfish.
It does not see our weighted belief as one input.

The v38 patch changes how full root-child scoring is performed. It increases
throughput but does not promise the same numerical scores as unmodified
Stockfish. An outer FoW tree can still be many plies deep: “Stockfish depth 1”
describes each frontier scoring request, not the depth of our entire tree.

The C engine converts a centipawn score to a bounded utility:

```text
value = tanh(centipawns / 400), with sign adjusted to our side
```

For example, +100 gives about +0.245 and +400 about +0.762. These are heuristic
utilities, not calibrated win probabilities. Exact FoW terminal handling
overrides the heuristic, and our own immediately fatal root move has default
utility −2 rather than the ordinary −1 loss value.

## Where regret minimization happens

An **information set** groups decision nodes that the represented player
cannot distinguish. The same action probabilities must be used throughout
that group. The solver operates on this constructed local tree, with current
Stockfish frontier values. It does not compare today's result with old arena
games when updating regret.

For an action `a` at information set `I`:

```text
instantaneous regret(I, a)
  = sum over nodes in I of
      chance-and-opponent reach × (value of choosing a − current mixed value)

R_new(I, a) = max(0, R_old(I, a) + instantaneous regret(I, a))

next strategy(I, a) is proportional to
  max(0, R_new(I, a) + latest instantaneous regret(I, a))
```

The last line is the predictive regret-matching+ step. Player updates
alternate. If every positive term is zero, the strategy is uniform. New
information sets initially favor their best scored child. The generic solver
also stores a strategy-sum array, but deployed move choice uses the **current
last iterate**, followed by argmax, rather than the averaged strategy.

For a tiny example with reach 1, suppose A is worth 0.6 and B 0.2. A 50/50
mixture is worth 0.4. Their instantaneous regrets are +0.2 and −0.2, so the
update favors A. In the actual game, these action values depend on the
opponent's strategy and all represented indistinguishable nodes; they are
recomputed as search grows.

Regret minimization is learning **inside one decision calculation**. These
regrets are discarded afterward. It is distinct from fitting model weights
across replay games or training PPO parameters.

## Why information-set keys are not the whole solution

Suppose our hidden rook is on a1, while the opponent's observations would
also allow it to be on h1. Our own current belief correctly fixes our rook
on a1. A search containing only those boards does not automatically contain
the h1 possibility relevant to the opponent. Giving nodes an observation
history hash cannot create that missing possibility. Future hidden actions
inside the tree can share opponent information sets, but that does not restore
all uncertainty about earlier private actions.

Common-knowledge closure follows chains of what each player cannot
distinguish; it can be much larger than our own information set. Obscuro's
knowledge-limited construction addresses this through a bounded construction,
a carried reference strategy and boundary values. This is not equivalent to
adding more copies of the same sampled current boards. Its treatment of fresh
samples also intentionally permits singleton opponent information sets.

Our deployed v38 omits that complete construction. M4 implements experimental
parts, with failed continuation/match evidence. This limits what we can claim
about solving the correct full-game information problem, even if the local
CFR implementation is arithmetically correct.
[Current comparison](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/358-astra-current-obscuro-gaps.md).

## What the guards guarantee—and what they do not

The main deployed root screen combines king risk with 0.9 times queen-loss
risk. Queen loss uses a default four-pawn net-loss threshold. It compares
candidate moves against the lowest estimated risk under two weightings,
normally with a 0.02 margin. The broader risk calculations stride across at
most 20,000 retained worlds. If the combined dual-weight test excludes
everything, it falls back to the sharpened test.

This can exclude dangerous moves that the 32-world search missed. It cannot
guarantee survival on the real board: that board may be absent, its risk may
be underweighted, the safest estimated move may still be unsafe, or an
unmodelled longer sequence may decide the game.

There is also a draw-modelling limit. The explicit FoW terminal checks in
`gtcfr.c` cover king loss and no-move loss; that builder has no explicit
threefold-repetition or 50-move draw check. Stockfish receives the hypothetical
halfmove counter and can reflect ordinary-chess draw tendencies, while the
front end heuristically discourages repetition when ahead. Neither is a full
history-aware implementation of the referee's draw rules in the outer FoW
tree. This is a source-level limitation, not a measured explanation of a
particular arena loss.

## Questions to practice answering

1. What persists between moves? What persists between games?
2. Why is a complete board insufficient to describe a player's information?
3. Why can better opponent-move prediction fail to improve play?
4. Why does a rare observed loss not by itself prove miscalibration?
5. Why is argmax over a stochastic search different from playing its mixed strategy?
6. What would we need to claim low full-game exploitability? We have not measured it.
