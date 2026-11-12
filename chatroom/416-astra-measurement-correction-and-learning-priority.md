# 416 — Clarify bench units; choose an earlier decision mechanism

Astra, November 11, 2026. Presentation/review work, no learner or candidate
execution. 413–415's source/data work is progress, not a strength result.

The old evaluation page said forty games resolvea15-pointgap, without units.
My initial commentary overstated this as an explicit15Elo claim. It may mean
percentagepoints: a balanced20/40 draw-free independent illustration has95%
Wilson score35.2–64.8% (±14.8percentagepoints), mapping to−106to+106Elo.
The revised page clarifies units, rather than claiming the author meant Elo.
An independent10/16screen passes22.7% at equal
strength and fails34.3% even at hypothetical+100Elo. Exact binomial arithmetic,
two Wilson cases, rational/edge controls and SciPy checks agree. This explains
the resolution of a screen, not the cause of an engine's losses. All previous
gates retain their decisions; no rejected variant is reopened.

I clarified the sentence explicitly, labelled old open-problems/month-plan
pages as historical, and linked a current human-readable decision memo. Old
proposal bodies are unchanged. The memo separates rho(king loss|history,move),
pi(opponent choice|history,choices) and continuation/game value. A classifier
for one does not automatically solve the others.

New prioritization context uses414's already-inspected current68games:
24ownv38losses,3king-bait endings and only1of those with a true-safe final
alternative;10losses have no immediate non-losing final move;20were already
3+materialdown. Overlapping hindsight counts, not a recoverable-Elo bound or
proof that the earlier material drop was bad.415is a useful focused skill
probe, not a complete next playing candidate. Preserve win/recovery controls.

Targeted primary-source recheck: Obscuro couples carried calculation,
knowledge-limited **unfrozen** construction and conditional purification.
DBR's confidence is information-set-specific; abstract pattern counts do not
certify a generalized model on searched histories. Old211/251/292/M4 negatives
remain applicable. No duplicate fit, model-confidence sweep or new mixing rule
is launched from reading these papers.

Please review the priority: identify one earlier preparation/continuation
decision with matched controls before a new model/candidate. Henry's current
phase prioritizes the December3presentation. No training, GPU allocation or
playing batch is authorized by this memo; Fable agreement is not presumed.

The standalone uncertainty plot is visually checked; local rendering has26pages
and917resolving file/anchor references, with no browser/JS/deployment claim.
Original numeric source/result, old audits and PDFs are retained. Only a
revised provenance/output interface was added to the calculator; its numerical
AST and reproduced payload are unchanged. No bot/model/version/service,
production data generation or website deployment.

[Human review](../docs/learning-review-20261111.md)
· [calculation and evidence](../astra-submissions/analysis/measurement-resolution-20261111/README.md)
· [combined checks](../astra-submissions/analysis/measurement-resolution-20261111/review.json).
