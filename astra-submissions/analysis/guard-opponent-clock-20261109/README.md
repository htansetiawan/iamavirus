# Matched Misty panel with verified live clock budgeting

This is a fresh comparison after the earlier harness disabled Misty's clock
manager. That earlier run remains failed: three opponent timeouts, zero
usable strength games, 29 unstarted games. It is not resumed and its apparent
wins are not strength evidence. The candidate's independent 10W–1D–5L pilot
against exact v38 remains valid.

The same installed Misty 0.1.3/v1.6 now runs with FOW_V2_CLOCK_TIME=1 and no
fixed budget, matching its own clock-aware policy. A thin checked adapter
preserves the original observation/action handling and asserts that the
actual strategy has clock budgeting enabled. At 180+2 its initial policy
budget is five seconds. The disabled setting is rejected before ready in
0.16 seconds. Full-clock preflight covers four actual Misty turns across both
colors, with 180-second and roughly 177-second prompts; they finish in
5.00–5.03 seconds. Both native arms also pass both-color protocol probes.
No probe uses the old fixed 50 ms budget for Misty.

A new queue uses seeds 2752000 onward: 32 games, 16 candidate and 16 exact-v38
controls, eight blocks with both colors and arms. First arm alternates and
matched cells share engine/opponent seeds. Playing native bytes, candidate
mask rule and thresholds are unchanged. The gate requires all 32 clean games,
at least eight candidate points and at least two more points than the control.
It only earns candidate review, not an Elo claim or automatic upload.

The audited harness from the prior run supplies worker management and
process-group control; both that source and the new clock-checking wrapper
are pinned, along with every playing dependency. Three lanes on cores 0–5
freeze off-turn groups and charge buffered observations on the next turn.
The batch has a four-hour bound and each first attempt 2,450 seconds. No
started game is repeated; a technical fault stops new games globally while
in-flight games may finish. A full game must fit the remaining batch bound
before its attempt starts. This is scheduling control, not a security sandbox.

The opponent is local Brian Liou Misty, not verified current arena bytes or
Brian Hu Zhang's original Obscuro. Seeds do not eliminate all wall-clock
search variability. A separate final referee and process-cleanup audit is
required. The preflight-only partial setup was preserved when a missing
audit dependency was caught; no games were started during that correction.
The earlier audit also corrected a strict string check to parse decimal
clock input as a number. Neither setup correction changes playing outcomes.

Source and final plan will be pushed before launch. No GPU work, data ingest,
model fit, numbered release or arena action is part of this comparison.
