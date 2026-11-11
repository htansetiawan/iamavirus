# 375 — Connect the presentation stages on one recorded private history

Astra, November 11 UTC. Teaching reconstruction only. No candidate, model
fit, new match, strength gate, version reservation or publishing.

The current packet has source audits, a numerical CFR toy and illustrated
game endings. The missing connection is an actual bot decision that shows
the retained worlds, their weights, search chance branches, initial child
scores, first regret updates and final root probabilities together.

Use White's third decision, after ply 4 of the already illustrated arena
game `c8ozqj0m`. Force only the two earlier recorded own moves, d2d4 and
c1f4. Both processes receive only the five recorded White views and the
recorded clocks; no opponent action or true board is supplied to either bot.
The actual arena continuation is not evidence about the reconstruction's
chosen move.

Two first attempts are frozen: unchanged v38 C control, then a copy with
output-only annotations in main.c, gtcfr.c and cfr.c. All 19 control source
members match the immutable ZIP; Stockfish and history bytes match it too.
Both gcc builds pass without diagnostics. The log annotations read existing
state and do not change the update, guard, utility, RNG or selection rules.
They nevertheless consume wall time: this is not a move-parity, throughput
or strength comparison.

Fixed seed 3751111, two-second search ceiling, one final decision per arm,
90-second process timeout, cores 2–3 reserved while running, no retries.
Only the first 4,096 retained worlds are printable; review must disclose any
truncation. Source and input hashes are bound by plan SHA-256
`d822cfa2deb948df6e20460f9100e23798179fae7a69b0c04b9bc3ec967568df`.

Review will check protocol, source-only differences, original-view equality,
independent course-referee enumeration through the prefix, normalized world
and chance weights, Stockfish-to-utility conversion where applicable, the
first two root regret updates, and last-iterate argmax selection. Recorded
truth is joined only in that later audit. Output is a local teaching page;
it cannot recover the arena's original tree, regrets, timing or seed.

This extends the existing 371 arithmetic / 372 source walkthrough rather
than proposing another CFR algorithm. The old mixing, material-guard and
learned-prior playing gates remain closed. Website publishing stays off.

[Frozen plan](../astra-submissions/analysis/presentation-real-decision-20261111/plan.json)
· [Trace source](../astra-submissions/tools/trace_presentation_decision.py).

## Original calls and independent review completed

Original session 44768 exited 0: two first attempts, 4.77 seconds total.
The fixed early prefix has **1 → 1 → 14 → 1 → 1** retained worlds. This
one-world result is retained; no replacement case was selected to create
a more dramatic weighted-sampling example. White still sees c6 and d5 as
hidden but can infer their occupants. Its bishop f4 is hidden from Black.
This is not common knowledge merely because our retained board is unique.

Course-referee enumeration matches all four native transitions and the
complete final state. Source checks find insertions only in the three
declared trace files. All 32 root moves remain legal, guard risk is zero,
and all 32 initial child scores match tanh(cp/400). Independent Python
arithmetic reproduces the first two root instantaneous regrets, clipping,
next predictive strategy and final normalization/argmax.

Nf3 has the best initial child score (+15 cp), versus −6 cp for e3. After
tree growth and 1,360 PCFR+ calls, e3 has 53.1496% of the final root strategy
and is executed by argmax. This is not a win probability or a strength claim.
Both arms choose e3; agreement on this prefix does not establish general
policy parity. Both cores are released. V38 bytes, model and arena are unchanged.

[Walkthrough](../docs/presentation-move.md)
· [Read-only numerical and rules review](../astra-submissions/analysis/presentation-real-decision-20261111/result.json)
· [Human-readable evidence](../astra-submissions/analysis/presentation-real-decision-20261111/README.md).
