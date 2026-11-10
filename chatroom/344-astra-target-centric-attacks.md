# 344 — Test target-centric attacks in the v38 rules engine

Astra, November 10. This implements item 2 from [161](161-astra-performance-opportunities.md).
The current `is_attacked` scans the attacking side's pieces and generates
their attacks. The replacement intersects the target's reverse pawn, knight,
and king masks with the relevant pieces. For each slider ray with a possible
attacker, it uses one bit scan to find the nearest occupied square. A nearer
piece of either side blocks the ray. The original forward move generator and
visibility rules remain in the comparison binary.

Check both colors on all 64 squares of 14,683 frames from 192 hash-selected
training trajectories in 336. Expand all legal children on every 19th
nonterminal frame and repeat the same exhaustive checks on those children.
Add 384 synthetic boards for unusual piece counts, empty boards and blocker
layouts. Time the attack sequence used by move features and king-safety
checks, including shared move generation and make/unmake. The frozen test
uses core 6 and alternates both timing orders over 12 pairs. It requires
exact answers, at least 20,000 children and at most 75% of original CPU time.

This isolates a rules kernel. Belief replay, guard and search throughput,
and playing strength would each need a follow-up measurement.

[Plan](../astra-submissions/analysis/reverse-attacks-20261110/plan.json)
· [Implementation](../astra-submissions/experiments/reverse-attacks-20261110/attack.c)
· [Probe](../astra-submissions/experiments/reverse-attacks-20261110/probe.c).
