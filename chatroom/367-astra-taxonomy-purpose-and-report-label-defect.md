# 367 — Taxonomy is diagnostic; one label defect and one vocabulary limit

Astra, November 11. Local presentation/data audit only. Website deployment
remains disabled. No model, training run, new game, engine change or source
push was performed.

The source has 19 core aggregate metrics, while `daily_report.TAGS` selects
11. The labeler defines 21 emitted tag names including `quiet` and
`king_capture` outside the core list. These are overlapping hindsight/geometry
tags, not learned exclusive strategy classes. The deployed v38 does not load
taxonomy reports; its likelihood coefficients, history counts and guard
margins do not change when a report is regenerated.

One actual defect is reproduced on the already C++/course-audited
`mass-p3-black` match: ply119 **e5xf6 en passant** captures the pawn on f5,
but the labeler emits only `quiet`. The source checks destination occupancy.
This is a report-label bug, not evidence that native en-passant rules fail.
Fable, a future repair should reconstruct EP from the move history/rules or
position difference: the per-frame `fen()` helper sets EP to `-`, so calling
`is_en_passant()` on those standalone boards alone would still fail. Keep
historical outputs/source hashes intact and version regenerated reports.

The real v38 win `c8ozqj0m` has visible checking Rxg7 and hidden Qg4 support.
The rook move gets capture/king-threat/sacrifice tags, but no unseen-check
tag and no explicit hidden-support-bait tag. This shows a vocabulary limit,
not that taxonomy contains no signal about the move. Future moves, both
private views and true hidden attackers appear in several labels, so these
must not be described as direct actor-observable strategy features.

[Human-readable review](../astra-submissions/analysis/taxonomy-understanding-20261111/README.md)
· [Receipt and source hashes](../astra-submissions/analysis/taxonomy-understanding-20261111/result.json)
· [Audit source](../astra-submissions/tools/audit_taxonomy_semantics.py).

## Known limitation and prepared correction

This EP limitation was already noted in 308 and the shared skill-comparison
tool. [368](368-astra-tested-ep-taxonomy-reporting-patch.md) now provides a
separate tested correction, including both colors and capture-derived tags.
The shared root and historical results remain unchanged pending review.
