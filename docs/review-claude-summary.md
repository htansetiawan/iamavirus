# Review 3 — What would actually move us toward first place?

**Astra · 25 October 2026 Pacific · Review of the summary pasted by Henry**

The summary is a useful implementation inventory. Its separation of deployed
code, experiments and data infrastructure should stay. **Its proposed “ideal
system” is not yet a justified development plan.** Some limitations concern
representation, objectives and evidence; additional compute alone cannot fix them.

## Corrections that affect decisions

| Claim or omission | Review finding |
|---|---|
| The appendix describes deployed v35 defaults | It mixes releases. The immutable v35 ZIP matches `97b60f1` in the four audited engine files. Its sources do **not** contain `MIST_FOG_HAZARD`, `MIST_KING_MOVE_HAZARD`, `MIST_HAZARD` or `MIST_GUARD_UNIFORM`. Document checkout-only controls separately. |
| Belief limitations are primarily the board cap | v35 merges identical boards and keeps **one representative opponent history**. Two histories can reach the same board while giving the opponent different knowledge. This approximation occurs before the cap and can affect both prediction and search. |
| Reports tell us where Elo is being lost | The Elo-flow lookup compares hyphenated snapshot dates with unhyphenated game dates. Three historical timestamp reproductions all selected the latest cached snapshot. Those historical point-flow claims need recomputation. |
| “Top six” means today's leaders | The insights script hard-codes the older six, omitting Crimson Fog and Mist Opportunities. Keep that group for longitudinal comparison, but label it and add the current leaders. |
| More compute, mixed play and learned values remove the remaining defects | This is a hypothesis. A learned scalar board value cannot recover discarded opponent histories or actions removed before search. A mixed strategy from an inaccurate game model is not necessarily safer or stronger. |
| Failed hazard corrections prove double-counting | They establish unsuccessful candidates, not a uniquely identified cause. Calibration, information loss, placement in the tree and changed behaviour remain alternative explanations. |

The source checks and reproducible timestamp example are in the
[technical audit](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/competitive-review-20261025/README.md).
That audit also corrects the “24 of 40” statistic: it counts games exceeding the
100,000-board cap, not games proven to have lost the true board.

## Where we are

At **26 October, 00:09 Boston time**, the public snapshot places v35 at
**1909 Elo, rank 10**; Greek Gift is **2379**, rank 1. This updates the summary's
earlier snapshot, without attributing the change to an engine improvement.
The latest cached seven-day report gives approximately 5% score against
Greek Gift v25, 32% against duck v6, 42% against Instructors v4 and 48% against
Mist Opportunities v2. These are descriptive scores; the timestamp defect affects
Elo expectations, not the underlying result counts.
[Frozen evidence](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/competitive-review-20261025/source-audit.json).

**Duck is a practical near-term target; Greek Gift remains the strategic test.**
Improving against mid-table opponents while ignoring the leader can raise our
rating without teaching us the skills needed for first place. We do not know the
leaders' private algorithms from their replays.

## What to borrow from successful systems

| Primary source | Useful lesson and boundary |
|---|---|
| Zhang and Sandholm's [Obscuro](https://arxiv.org/html/2506.01242v2) | Imperfect-information search can be very strong with Stockfish leaves. Its purification ablation scored 70.2% for the full system against the variant without that restriction: blanket randomisation is not an established upgrade. Its knowledge-limited solving has assumptions; copying component names does not reproduce its guarantees. |
| Brown and Sandholm's [Libratus](https://noambrown.github.io/papers/17-Science-Superhuman.pdf) | The poker champion used opponents' actual actions to identify missing branches worth improving. Our adaptation: spend learning effort on demonstrated strategic gaps, then retain the improvement across games. |
| [StrangeFish2's tournament report](https://proceedings.mlr.press/v220/gardner23a/gardner23a.pdf) | The RBC winner prioritised hypotheses and information according to decisions and outcomes. Minimising uncertainty alone did not explain strength. RBC has a separate sensing action, so transfer the principle, not its rules or rating. |
| Lanctot and colleagues' [PSRO](https://proceedings.neurips.cc/paper_files/paper/2017/hash/3323fe11e9595c09af38fe67567a9394-Abstract.html) | Train responses against a mixture of policies and measure the resulting payoff matrix. This addresses overfitting to one sparring partner; our stale replicas are insufficient evidence of current arena strength. |
| Schmid and colleagues' [Student of Games](https://pmc.ncbi.nlm.nih.gov/articles/PMC10651118/) | Search generates useful training questions and learned models improve subsequent search. Its success motivates a persistent learning loop, but its public-belief representation requires adaptation to this game. |

## Recommended order

| Priority | Concrete next work | Evidence required before expanding it |
|---|---|---|
| **0 — Restore trustworthy inputs** | Fix timestamp lookup, explicitly label opponent cohorts, repair training-data paths, pin deployed configuration | Recomputed report; readable, dated training manifests; release-derived settings. A bounded prerequisite, not another research programme. |
| **1 — Identify the recoverable gap** | Use a small, frozen, recent panel including wins and draws. Separate missing worlds, underweighted threat families, lost opponent histories, excluded escapes and frontier mistakes | One intervention must change the predicted failure mechanism at equal clock cost. Selected fatal positions cannot estimate how common each cause is. |
| **2 — Build a history-aware learned challenger** | Train a compact model to prioritise actions and hypotheses using search comparisons and actual outcomes. Preserve rule-legal alternatives and model the opponent's available information | Held-out tactical decisions and offensive conversion improve; CPU inference fits the arena. Then compare standalone and search-assisted play against a frozen diverse league. |
| **3 — Promote through real competition** | Test the candidate against current arena versions after local gates; freeze the comparison cohort and decision rule beforehand | Complete-game scores, both colours, uncertainty and unchanged clock reliability. Lower imitation loss is not a promotion criterion. |

I would start the learning lane with **one composable skill: recognising and
creating concealed forcing threats while preserving an escape**. Train on
observation histories and alternative continuations, rather than player-name
labels. Measure defence and attack separately: escaping hidden attacks, inducing
opponent mistakes, and converting advantages into wins. A specialist that works
can become a module in the general controller.

This refines my earlier learned-controller recommendation: the interface must
retain the alternatives and histories the learner needs. In our 80-position
diagnostic, every true escape was excluded in five cases, and four times the
search budget changed fatal choices from 10 to 11. Neither finding establishes
population loss rates, but both rule out blindly distilling that teacher.
[Teacher audit](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/deeprl-table-audit-20261025/teacher-readiness-report.md).

## Spend resources on decision quality

Reuse the native simulator and persistent teacher processes. Start with a
retrieval baseline over observation-history motifs before adding learned codes;
use VQ/RVQ or quantisation only when measured quality or runtime justifies them.
Validate splits by whole game and time, including held-out opponent versions.
True boards can supply training labels, but must not enter the deployed actor.

Choose work by **recoverable match points, confidence and delivery cost**, not
promised Elo or algorithm prestige. Reserve one delivery lane and one bounded
architectural challenger. At the next 24-hour committee review, show the exact
artifact, games and uncertainty, resources spent, what was falsified, and the
next continue/revise/stop decision. No automatic extension.

This review changes the proposed priorities; it does not launch training,
change the engine, or authorise an arena release.
