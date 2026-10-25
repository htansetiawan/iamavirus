# Astra 150 — Review the architecture against the literature

2026-10-25. Henry asked what Deep CFR is, how it differs from Obscuro, and which
two or three strong Dark Chess techniques could be combined. He explicitly
allows replacing the current architecture.

The [comparison and proposed experiment](../astra-submissions/specs/dark-chess-literature-20261025.md)
distinguishes demonstrated strength, historical baselines, learning experiments,
and public reimplementations. It links the primary papers and author reports.

The main addition to our shortlist is ESCHER. Its neural regret-learning result
is relevant, but its Dark Chess evaluation omitted observation history and did
not establish superiority over the leading search engines. This corrects the
older research memo's categorical dismissal of published FoW self-play learning.
The document also records specific evaluator, ablation, and clock corrections
to that memo. Please use the correction rather than reusing its numerical claims.

My proposed comparison is a credible search reference, a history-aware learned
actor, and their hybrid, with equal total turn budgets. Learned proposals must
reach the C search before uncertain guard exclusions; critic targets and actual
actor inputs must remain separate. Preserve ESCHER's sampling contract in its
own learner. Search distillation is a different data stream, with no automatic
transfer of equilibrium guarantees or PPO likelihood ratios.

The existing code is not a requirement for the final design. Retain components
that win measured comparisons. The spec proposes a bounded first pilot and a
24-hour committee checkpoint; it does not authorize or start a new GPU run,
alter your source, create a release, or claim an Elo improvement. Please review
the architecture choice before assigning implementation ownership.
