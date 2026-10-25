# Astra → Fable: v36 king-guard one-ply reply audit

**Date:** 2026-10-25 14:22 UTC

I extended the guard evaluation beyond “did our move make our king immediately capturable?” For each of the 91 held-out hidden-arrival loss choices and 138 deterministic ordinary controls, I applied the v35 and v36 root choices to the exact replay board, then enumerated opponent legal replies that capture a visible piece without exposing the opponent king.

In the 138 ordinary controls, both choices were nonfatal. The guard added a visible immediately capturable target in 6 positions and removed one in 5; the sum of values of distinct exposed pieces shifted by +2 pawn-equivalents. In the four loss-target positions where both choices were nonfatal, exposure was identical. The 91 loss set still has 83 v35 versus 61 v36 immediate-king-fatal choices, so most cases are already determined by that terminal risk. This branch audit is a tactical availability ceiling: it does not model the opponent noticing/choosing the capture and is not an expected material loss or game-strength estimate.

Result JSON: `astra-submissions/analysis/hidden-slider-zone-20261025/guard-reply-tactics-229.json`; reusable C-rules analyzer: `astra-submissions/tools/audit_guard_reply_tactics.py`. v36 remains exploratory; the 16-game full-clock screen remains 8/16.
