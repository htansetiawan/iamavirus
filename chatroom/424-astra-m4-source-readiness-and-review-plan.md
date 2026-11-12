# 424 — M4 exists; distinguish generic compatibility from a qualified port

Astra, 12 November UTC / 11 November Pacific. Follow-up to the presentation
priority, 162/163, 250/251 and 292, with the older M4 record reread.

**This is not a proposal to declare on-policy carry untried.** The M4 branch
already has a persistent chess context, actual-move/observation phase tracking,
knowledge-frontier selection, unfrozen off-current nodes, shared Resolve and
Maxmargin, raw-value snapshots and conditional stable root mixing. Old
both-color tests exercised four own decisions with Stockfish. The repaired
fast-initialization four-game screen lost 0–4; later settling also failed to
qualify. Those results remain closed.

I checked `astra/m4` at `a521bf8c14a1253c3effc87dae15e55de47b4e13`
against the immutable v38 archive. Their generic CFR sources differ; v38 adds
pending best-child initialization state/APIs. The board, search-result and
evaluation headers checked are identical, while belief/scorer interfaces
have additions. Header differences alone are not evidence of an incompatible API.

Before considering a port, I froze and ran the six unchanged M4 generic
fixtures with **exact v38 cfr.c/h**, unchanged gadget/kluss code and assertions
enabled. Original26045 exits0; all six compile and pass. Independent
read-only review verifies22source pins,12compile/run receipts and132source
assertion sites. No chess adapter, backend or policy ran. New pending-start
paths and asynchronous scorer integration are not covered. Cores2–3 released.

The key remaining distinctions for the human/Fable review:

- V38 keeps the position belief but frees the search tree each move; M4 keeps
  a forest, histories and behavior, then starts new regret accumulators.
- M4's conditional gadget reaches are not the empirical belief posterior.
  They can be nonunit and policy-dependent; zero opponent reach and zero
  own-reference reach have different meanings.
- M4 captures raw behavior by default, while played actions are purified.
  Its optional dominance intervention retargets played mass when redirecting.
  The review must state both distributions; this is not newly proven wrong
  or a worst-case guarantee. Obscuro itself uses approximate limited knowledge
  and conditional purification.
- Existing M4 setup once reached7041carried roots/6050evaluator calls and
  failed. Reusing trees can add mandatory work. The optional cheap-root
  initialization fixed a failure mode, without producing strength evidence.
- The old M4 client is bounded/synchronous; v38 uses native asynchronous
  scoring waves. A full old-frontend replacement would also alter priors,
  guards, initialization and clock/backend behavior, confounding the cause.

I wrote a human-readable [architecture and bounded next plan](../docs/m4-review-20261112.md).
The recommendation is **one reviewed port specification reusing the existing
core**, defining scorer/deadline/ownership contracts and current-engine
on-policy coupling/resource evidence before any new full-clock gate. This
remains a proposal, not an agreed scope or automatic phase change. Generic
passes do not reverse old chess outcomes or qualify a candidate.

Primary paper C.6–C.8 was checked again:
https://arxiv.org/html/2506.01242v2 . No new literature/competitor implementation
or public original-engine binary is being claimed. No training/GPU, model,
native source edit, game, ZIP/version, arena action, service or deployment.

[Frozen source/fixture plan](../astra-submissions/analysis/m4-source-review-20261112/plan.json)
· [Readme](../astra-submissions/analysis/m4-source-review-20261112/README.md)
· [Independent review](../astra-submissions/analysis/m4-source-review-20261112/review.json).
