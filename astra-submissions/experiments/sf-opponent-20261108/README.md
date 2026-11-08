# Matched opponent gate for the proposed v38

The unchanged all-child Stockfish candidate passed its frozen 16-game pilot
against v37: 11W–1D–4L, with all first attempts independently audited. Test
generalization against the authentic local Misty 0.1.3 package using v37 as
control. This is not asserted to be the current Mist Opportunities arena code.

Freeze 32 full-clock games: eight seed blocks, both colors, candidate and
baseline each playing the same Misty seed. Each arm gets 16 games. Alternate
which arm plays first within blocks. Standard start, 180+2, two lanes on
cores 0–1 and 2–3, four-hour batch cap. Keep the exact candidate/native/history
bytes from experiment 256. Do not add solver, guard, prior or time changes.
Seeds may not control every source of Misty or wall-clock search variation.

Preserve every started game and first result. Technical faults stop that lane;
never repeat a started game merely because a tool handle expires. Inspect
result/replay/started receipts and process ownership first. Referee checks,
clock and process-control audits, exact launch/binary hashes and color/seed
matching are mandatory before making any strength claim.

Advancement requires all 32 games and no technical failures, candidate total
at least 8/16 and at least two points above the 16-game baseline total. Report
all paired block differences and uncertainty; this development threshold is
not a statistical guarantee. A pass earns final package validation and a
human-review candidate for arena evaluation. A failure closes this unchanged
candidate for promotion; no extra games or parameter tuning on this panel.

The human requests v38 for review on 8 November (Los Angeles). Highest Fable
archive is v37 at preparation; recheck +1 at packaging and publication. The
release must include the exact scorer source/licence, original native source,
portable execution, hash manifest, prediction and fail-fast rule. No arena
upload is performed by this experiment.
