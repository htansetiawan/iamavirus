# Actor-input checks on the thirty newly cached games

The existing history tests already check event timing and separation of actor
features from privileged labels. This audit applies those contracts to the
unchanged, exposed thirty-game cohort reviewed in 389. It does not introduce
a privacy algorithm or evaluate a trained policy.

Both colors produce **60 player episodes, 5,054 delivered observation events
and 2,527 demonstrated decisions**. The original run checks all 323,456
square-events against a separate raw-square history accumulator: current
piece/unknown/empty encoding, last-seen content and age, prior own-move planes,
en-passant plane alignment, castling rights, phase/turn scalars, and Black's
rank reflection. Every demonstrated move and truth label is aligned to its
source frame. History-derived candidate lists match the validated board's
legal moves on all decisions; no candidate-mismatch samples are present.

For each of the 60 episodes:

- Changing privileged board labels, danger/return labels, validity flags and
  player/opponent metadata leaves planes, scalars and candidate arrays equal.
- A midpoint prefix produces exactly the same earlier features as the full
  event stream, even with later own actions present in the action dictionary.
- Changing one current action leaves its own decision and earlier features
  unchanged, while its later move-history planes change. This positive control
  distinguishes causal timing from a feature function that ignores actions.

These interventions test the data interface. They are not alternate valid
full-game histories or a complete proof about all information sets.
Special-rule coverage is limited to this cohort; original synthetic/parity
tests remain separate.

## Evidence

Original session 50806 exited zero once, in 2.85 seconds under the 180-second
cap. A separate receipt review independently derives the event, decision and
square counts from frozen replay lengths, checks both color receipts for every
ID, and reconciles source hashes, execution/result hashes and lease release.
That review is not a second feature reconstruction.

[Plan and source pins](plan.json) · [Result](result.json) ·
[Receipt review](review.json) · [Auditor](../../tools/audit_episode_actor_inputs.py)
· [Receipt reviewer](../../tools/verify_episode_actor_inputs.py) ·
[Original cohort](../daily-own-cohort-20261111/README.md).

Private per-episode receipts stay in
`data/astra-spool/episode-actor-inputs-20261111/`; the original replay copies
stay unchanged. No episode export, split, model, GPU, native build, game or
release was created. This is a check of episodes reconstructed with the
current builder, not the unfinished export's actual shard contents.

The observation-policy pipeline is retired from deployed v38. Its data checks
do not establish v38 strength or a quality result for a future learned model.
The independent cross-generation fold warning in 394 remains applicable.
