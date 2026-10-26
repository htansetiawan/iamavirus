# 162 — Fable: review of Astra's Obscuro, Misty and v35 claims

Henry asked Astra to explain Obscuro's contribution and Misty's implementation
and to confirm the understanding with me. Sources read for this note, 26 Oct:
the paper's v2 HTML (arXiv 2506.01242v2, including the appendices), Brian H.
Liou's public post on Misty (updated 15 Oct; no Misty source was read, the
clean room stands), and mist-c at 539d4e3 plus today's guard commit (main's
defaults equal v35's, 97b60f1). Verdict first: all four of Astra's claims are
correct. The precisions below are additions, not corrections, except where
marked.

## (1) Who wrote what: confirmed

Obscuro: Brian Hu Zhang (MIT CSAIL in v2) and Tuomas Sandholm (CMU). Misty:
Brian H. Liou, who writes that it "implements the architecture of Obscuro" and
is "guided by Obscuro, not a faithful reproduction of it", with every departure
tabled. Two different Brians.

## (2) The paper's contribution: confirmed, with the mechanics spelled out

- **KLSS (2021) and KLUSS.** KLSS removes nodes outside the order-(k+1)
  knowledge set and freezes the expanding player's nodes beyond the order-k set
  to the blueprint. KLUSS leaves them unfrozen and re-optimises them. The 2 in
  2-KLUSS is k = 2: the paper says this "essentially amounts to pretending" the
  order-2 knowledge set is the common-knowledge set. The paper states that KLSS
  and KLUSS "are not always game-theoretically sound in theory", are "often
  sound in practice", and that 2-KLUSS lacks worst-case safety guarantees, with
  a counterexample for KLSS. Astra's soundness caveat is exactly right.
- **"Improved alternate/gift values and Resolve/Maxmargin"** means three
  specific changes, not new gadgets. Alternate values use the blueprint's
  conditional values u(x, y | J) instead of best-response values. Gift
  estimates use counterfactual values instead of counterfactual best
  responses. The Resolve root distribution mixes a uniform distribution over
  opponent infosets with the blueprint-implied one. Obscuro picks Maxmargin
  when the opponent always exits in the Resolve gadget, Resolve otherwise.
- **One-sided GT-CFR.** Only the exploring player, alternating each iteration,
  plays the exploration profile: half uniform over the support of the current
  strategy, half the argmax of Q̄(I, a) = u(x^t, y^t | I, a) + C σ^t(I, a)
  √N(I) / (1 + N(I, a)) with C = 1 and σ the empirical variance of the Q value
  over visits. The other player plays its current strategy.
- **PCFR+ last iterate, purification.** PRM+ regret minimisers; the decision
  uses the last iterate (randomised stopping time, last-iterate convergence
  observed). Purification samples among the m ≤ 3 top actions (MaxSupport 3),
  only when the strategy is judged safe (value at least the pre-turn
  expectation), only among "stable" actions (in the support on every iteration
  after half the budget); under Resolve the top action is played
  deterministically; excluded mass goes to the top action.
- **Reuse between moves.** The previous tree is merged into the new subgame and
  the previous strategy is the blueprint. Appendix averages: tree 1,070,552
  nodes and 14,404 infosets, of which 181,421 nodes and 3,162 infosets carried
  over; search depth 10.7 plies; |P| average 17,264, usually ≤ 10^6.
- **Not "many boards plus Stockfish", not Deep CFR.** No learned network. Leaves
  are Stockfish 14, MultiPV, depth 11. The root sample is min{|P|, 256}
  positions drawn uniformly without replacement from P minus the sample
  (MinInfosetSize 256); the root chance node over an opponent infoset is by the
  opponent's reach probability. Self-play study at 5 s a move; human matches
  at 3 min + 2 s on a six-core desktop.

## (3) v35's fidelity: confirmed, with what the code actually does

- **Belief.** Exact enumeration, Zobrist position keys, an open-addressing set
  for deduplication, positions merged by key with one representative history.
  Log-weights from the fitted conditional-logit opponent move model
  (temperature 2.0) and the history-table prior. Cap 200,000 by weighted
  sampling without replacement (exponential keys, expected-linear selection),
  two threads. So "capped weighted P with history/move-model priors" is right.
- **Root sample.** K draws by weight with replacement (K = 256 at budgets of
  3 s or more, 128 below); a chance node over the distinct worlds with their
  draw frequencies. On the calibration set the median number of distinct
  worlds is 19. The paper's sample is uniform without replacement up to 256,
  with the opponent's reach only at the chance node. Ours is weighted; this is
  a real departure and the reason the guards exist.
- **Tree and infosets.** A fresh tree each decision. Flat arrays: nodes
  (type, player, infoset, first edge, count, value), edges (child, chance
  probability), per-slot regret, last instantaneous regret, strategy sum.
  Infosets keyed by each player's own history hash (its moves and views so
  far) in an open-addressing map. Every child of an expanded leaf is scored by
  one Stockfish 19 `go depth 1` MultiPV-256 call; value tanh(cp / 400);
  unscored children floored at the worst scored value; our own king-capturable
  root move is a terminal at −κ.
- **Solver.** PCFR+ with CFR+ clipping and the last instantaneous regret as the
  prediction; the decision uses the current (last-iterate) strategy. Pipelined
  with the two Stockfish workers (0.3 iterations per expansion). A 2.5 s suite
  decision builds about 80k nodes, 1,000 infosets and 700 iterations; the
  paper's trees are 13x larger with 11-ply leaves.
- **Expansion.** One-sided, the explorer alternates each pick. The explorer's
  rule is half uniform over the support and half the argmax of
  x^t(a) + √(N(I) + 1) / (1 + N(I, a)): the current strategy as a prior plus
  a visit bonus, with no Q term and no variance term. Astra's reading of
  `pick_once` is exact. The non-explorer samples its current strategy.
- **Decision.** Argmax of the last iterate after the exclusions (king and
  queen guards under the 0.02 margin rule, the repetition rule when ahead,
  view legality). No m ≤ 3 sampling, no stability test, no safety check: v35's
  "purification" is a plain argmax, closer to Misty's top action than to the
  paper's rule.
- **Missing, as Astra lists:** KLUSS at any k, the Resolve/Maxmargin gadgets,
  alternate and gift values, the blueprint, tree carry-over, safe mixing. In the
  paper's terms v35 solves an unsafe depth-limited belief subgame rooted at a
  weighted sample of P and ignores the opponent's reach outside that sample;
  the guards (risk measured on all of P or 20,000 boards) compensate for
  exactly that. The README's M4 row is empty.
- **Stockfish 19 at depth 1:** confirmed from the v35 zip's binary. The paper
  used Stockfish 14 at depth 11; Misty uses Stockfish 18 at depth 1.

## (4) Misty from its author's post: confirmed, with additions

Uniform belief ("not equally likely", but weighted equally), capped at 16
million with a uniform random sample above the cap; 32 root worlds (larger
counts lost head-to-head at fixed time); Rust belief enumerator (about 500x
the Python one, which stays as the reference oracle and fallback), Python
orchestration; the tree is discarded every move (a carried tree existed in 1.1
and was removed in 1.2); Resolve only, Maxmargin behind an environment variable
and never shipped; no reach gifts, "a single scalar margin, set to zero"; CFR
walks the whole tree every iteration, no sampling, no pruning; growth stops at
2,000 leaves and the remaining time refines the mix; Stockfish 18 at depth 1,
one thread, 16 MB hash; the top action is played (forced mixing went 0-7-1);
guards run last and veto hanging a major piece or walking into king capture,
replacing the search's choice on 17% of moves in eleven self-play games; nodes
keyed by observation history. Timing per move: equilibrium 69%, Stockfish 11%,
belief update 6 ms; about 45,000 iterations and 6,300 nodes in a 5 s move. The
post gives no hashing or container details.

## (5) Data structures: Astra's statement is right

The paper's appendix describes only the structure: a tree shared by one solver
thread and several expander threads, node states New, Expanded, Visited and
terminal, "no locks needed: all Expanded nodes are safe to access", a PRM+
minimiser created per infoset on expansion, infosets identified by the pair of
player and opponent sequences. No hash or key scheme is given, so the original
layout is indeed unknown. Our C layout is the one in (3): `Game` (flat node,
edge and slot arrays), `Tree` (leaves with a position and two history hashes,
a node-to-leaf map, the infoset hash map, per-slot visit counts) and `Belief`
(positions, per-position history hash and log-weight, the key set).

Nothing in Astra's four claims is wrong or misleading. The two points a reader
could take the wrong way: "improved Resolve/Maxmargin" is three modifications
to how the existing gadgets are fed, and v35's decision rule is an argmax, not
a purification in the paper's sense.
