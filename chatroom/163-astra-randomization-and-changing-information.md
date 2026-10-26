# Randomization and rapidly changing private information

Author: Astra. 2026-10-26. Follow-up to Henry's question about whether our implementation accounts for these two requirements.

Answer: partially, with concrete gaps. This is a source review, not a measured strength result, and does not change either candidate under evaluation.

## Action randomization

The paper's Sections 2 and C.7-C.8 distinguish mixed strategies, variability from stopping time, and restricted purification. Obscuro uses deterministic selection under Resolve and can mix among stable top actions under Maxmargin. It does not prescribe uniform random moves or unrestricted sampling of an unconverged strategy. Source: https://arxiv.org/html/2506.01242v2 .

Checked immutable v35 ZIP, `src/main.c:279`: `FOW_SEED` defaults to 1; the per-decision seed adds the decision count. Its `run.sh` does not supply a new seed. An external arena override is not established by this review. `src/gtcfr.c:420` returns the highest-probability root action. Consequently, sampled search and wall-clock variation do not establish that the executed policy has the probabilities computed by CFR. Even changing the search seed would not establish that equivalence.

The performance question is the played policy's susceptibility to a best response, not maximum action entropy. Example: converting a computed 60/40 policy to a 100/0 action can destroy the balance the solver found. Conversely, mixing in poorly evaluated actions can introduce blunders. Existing guards constrain posterior risk; they are not a worst-case exploitability guarantee.

## Changing private information

`belief_after_opponent` expands retained worlds through possible actions and filters them against the incoming observation; `belief_after_own` advances and filters after our move. These mechanisms permit the consistent-position set to grow and contract. Past observations are not literally forgotten: hidden moves change which current states remain possible.

Limits are relevant to this exact question:

- Weighted cap and time-based thinning can permanently discard the true trajectory. Recovery from an empty belief uses the current view and is not a reconstruction of the full past.
- `belief_after_opponent` groups candidates by position key, sums their weights, and keeps one representative opponent history (the heaviest candidate). Same board with different remembered observations can imply different opponent behavior. Board consistency alone does not preserve that distinction.
- Search keys information sets by history within a decision, but v35 carries no previous search/strategy into the next decision. We should not confuse persistent belief with persistent strategic commitments.

## Bounded follow-up proposed to Fable

1. Audit root distributions versus actual selected moves across recorded positions and controlled seeds/budgets; include a small imperfect-information game where a predictable policy is exploitable. If testing restricted mixing, preserve existing legality/guard exclusions and measure tactical regressions and adversarial response. This is an approximation until the resolving machinery is validated.
2. Tag replay positions with belief growth/contraction, effective sample size, truth retention, and history merges. On a bounded subset compare one representative history with several weighted histories per board at equal memory/time. Measure whether the extra distinction changes opponent predictions and decisions before expanding scope.

These are proposed priorities for review, not a claim of improvement or an instruction to interrupt Fable's material gate.

## Follow-up: common knowledge

Henry also asks about handling and consuming common knowledge. Shared rules, overlap of visible squares, our private posterior, and common knowledge are different objects. In particular, both players seeing a fact does not establish that they know the other saw it.

The paper's B.2 defines an indistinguishability graph on histories; its connected component is the common-knowledge set. 2-KLUSS uses a bounded neighborhood and retained search as an approximation rather than constructing that entire component. These modules are specified and exist as separate M4 work, but are not active in v35.

Implementation implication for our review: grouping opponent information sets only inside our retained private-board sample does not in general represent alternatives the opponent considers possible that our private observations exclude. That can distort modeled opponent behavior. More samples of the same private set cannot by themselves repair this structural omission.

Proposed small-game acceptance case: hold the physical board fixed but vary the players' observation histories; verify correct information-set grouping, preserve opponent-possible alternatives excluded by our view where the chosen subgame construction requires them, and measure best-response value with and without the bounded-knowledge/gadget construction. Do not describe this as full common-knowledge reasoning or a guaranteed-safe solve.
