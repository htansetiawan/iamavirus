# 358 — Which Obscuro components are absent from deployed v38

Astra, November 11. Henry asked this during the learned-prior playing pilot.
I rechecked the paper and the archived v38 C source. This updates the earlier
162 review and preserves its appended corrections.

| Component | Current implementation and evidence |
|---|---|
| Cross-turn tree and blueprint | `gtcfr_decide` creates a fresh `Tree` and frees its nodes, leaves, histories and solver at the end of every move. There is no carried search strategy in deployed v38. |
| 2-KLUSS and opponent-compatible past alternatives | Current roots are drawn from our own retained belief. The 251 review verified that extra histories only split independent copies under this model. It needs additional legally reachable possibilities with justified reach weights to represent useful uncertainty about our past hidden moves. M4 remains on `astra/m4`. |
| Resolve/Maxmargin, alternate values and gifts | The deployed source contains the plain sampled-root game. M4 implements experimental gadgets and carry components, with support, continuation-value and decision failures documented in its gates. Deployment needs a corrected complete construction. |
| Conditional-Q and variance expansion | Current `pick_once` uses `strategy_probability + sqrt(total_visits+1)/(1+action_visits)`. Experiment 234 implemented the conditional-value/variance component and scored 7W–9L, below its 10/16 screen. |
| Conditional stable-action mixing | Current `gtcfr_decide` chooses the maximum-probability final action. Experiment 203 tested a restricted stable mixture and scored 1W–3L. The full rule depends on the missing subgame construction. |
| Root-world coverage | V38 uses 32 weighted draws with replacement when Stockfish is active, and caps the maintained belief at 200,000 worlds with clock thinning. Its retained states and search sample can both omit truth. |

The paper's sampling reference is up to 256 uniform new positions without
replacement. Its action rule allows up to three stable actions under
Maxmargin and uses the top action under Resolve. Its leaf evaluation is
Stockfish depth 1. The old “depth 11” claim was a footnote-rendering mistake
already corrected in note 162. The paper's original six-core human-match
machine also differs from our arena compute budget.
[Primary paper, sections 3 and C–D](https://arxiv.org/html/2506.01242v2).

V38 already implements the PCFR+ solver, one-sided expansion framework,
observation-history information-set keys, best-child initialization and the
all-child Stockfish depth-1 scoring path. Its move choice can vary through
world sampling and search timing even though the final selector is argmax.

My ranking of the architectural gaps puts cross-turn reconstruction and
opponent information sets first. Those are coupled to blueprint reach and
boundary values. Copying extra histories alone did not change the useful
response problem in 251, and 292's native ancestry/reach test missed its
support criterion. Those earlier negative results define what a distinct
successor must repair.

The candidate aimed at arena v39 changes the opponent prior in the belief
update. The independent 355 replay test passed, and the full-clock 357 pilot
is running. It retains the deployed search construction. First two White
legs split 1–1. The first win has 89 independently checked frames. The
original remaining jobs and ten-point screen continue.

Fable, please review this current comparison, especially the cross-turn
construction, reachable alternative roots and conditional mixing. The
existing wording in `docs/methods.md` that information-set keys alone prevent
an overinformed opponent needs to be read alongside the 251 review.

[Archived v38 provenance](../astra-submissions/v38-manifest.json)
· [Opponent uncertainty review](../docs/opponent-uncertainty-20261102.md)
· [Conditional-Q playing result](234-astra-conditional-value-expansion.md)
· [Restricted mixing result](203-astra-stable-root-mixture-pilot.md)
· [M4 decision evidence](../astra-submissions/analysis/m4-alternatives-20261011/README.md)
· [Current match](357-astra-confirmed-prior-playing-pilot.md).
