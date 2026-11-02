# 249: amortize the existing MultiPV evaluator

The current search spends most of its move budget in leaf evaluation. Caching
was rejected in note 055: few requests repeated and warm Stockfish scores were
context-dependent. This experiment instead learns the complete vector of
ordinary Stockfish-scored moves from one parent-board encoding. It seeks
cheaper approximations of an existing teacher, not a claim that perfect-
information values solve Fog of War.

Reuse experiment 237's saved MultiPV outputs. Select 3,000 TRAIN games and
500 VALIDATION games by salted ID hash, all available selected parents, without
outcomes or teacher scores. Do not use its TEST fold. Remove duplicate canonical
parent inputs across folds, keeping training first. Parent state includes
pieces, side, castling, en passant and halfmove clock; no outcome, next move,
opponent identity or observed private history enters the student. At runtime
this input would describe a hypothesized world, never arena-provided truth.

Train only moves actually scored by Stockfish; do not infer missing-line
values or copy historical replies onto counterfactual boards. Verify recorded
values equal tanh(cp/400) from the parent mover's perspective. Terminal and
unsupported moves remain outside this learned interface and must retain exact
native handling in any later integration. Report their exclusion counts.

One fixed compact architecture: 128-dimensional piece-square embeddings plus
castling/EP/halfmove terms, clipped sum and 64-unit parent encoding. Every
candidate queries this shared encoding with source/destination embeddings,
promotion, moving-piece and destination-piece codes; a 32-unit head outputs
a tanh value. No attention sweep or replacement of the playing source.

Loss is per-parent mean squared value error plus 0.02 times listwise KL at
temperature 0.2. Parents are inverse-count weighted within games. One seed
2491102, AdamW 0.001, weight decay 0.0001, gradient norm cap 1, batch 256,
32 epochs, cosine schedule. Select epoch by equal-game validation MSE. One
GPU run capped at 20 minutes, only after a fresh idle-device check; never stop
an existing service. CPU preparation uses cores 0–1; no new Stockfish searches.

Development advancement requires all three: equal-game mean absolute value
error <=0.08, mean teacher-value regret of the student's best scored action
<=0.05, and frequency of teacher regret >0.5 <=1%. These are approximation
requirements, not Elo or safety guarantees. A pass earns native export and
a genuinely separate search-frontier test; a failure closes this architecture
without tuning on these results. Native feasibility subsequently requires a
payload <=1MiB and >=5x faster complete parent scoring than the original SF
path on matched inputs. Actual arena-budget decisions and complete games are
still required before any release.

The existing validation games have guided earlier outcome models; this is
explicitly development data with a different teacher target. Stockfish's
mutable state makes targets noisy, and played parents differ from searched
leaves. Neither limitation is erased by a low regression loss.

Method motivation: [Policy Distillation](https://arxiv.org/abs/1511.06295)
studies learning compact policies from teacher action values. [Stockfish's
NNUE documentation](https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html)
motivates sparse board encodings for CPU inference. This prototype implements
neither paper's full system and claims no inherited strength guarantee.
