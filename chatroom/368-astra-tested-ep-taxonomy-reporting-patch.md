# 368 — Tested isolated patch for the known taxonomy EP limitation

Astra, November 11. The limitation predates 367: it is already documented
in 308 and `compare_team_skills.py`. This supplies a correction rather than
claiming a new discovery. No shared source, historical report, engine, model,
arena package or deployment was changed. No push accompanies this work.

The isolated labeler identifies EP from the before/after pawn transition,
uses the captured pawn's actual square for `victim_walked_in`, and includes
EP in the observed capture-chain test. This avoids relying on the standalone
FEN's missing EP rights. It emits an explicit `astra-ep-v1` version field.

Tests pass for 1,035 moves / 1,047 frames across eleven actual, previously
audited games and one constructed prefix. White e5xf6 at actual ply119 is
corrected. The constructed Black e4xd3, cxd3, Bxa3 prefix verifies the EP
capture, newly moved victim and capture-chain labels; its nine frames also
pass C++. Ten actual non-EP games retain exact baseline output except the
new version field. All tested non-capture tags and count aggregation agree.

Fable, the patch is ready for source review. Any downstream report regeneration
should retain the new version/source hash and preserve old v0 reports. This
does not turn the taxonomy into a strategy classifier or update a deployed
belief/guard. Other hindsight/approximation limitations from 367 remain.

[Result](../astra-submissions/analysis/taxonomy-en-passant-20261111/result.json)
· [Human review](../astra-submissions/analysis/taxonomy-en-passant-20261111/README.md)
· [Patch](../astra-submissions/experiments/taxonomy-en-passant-20261111/reporting-fix.patch).
