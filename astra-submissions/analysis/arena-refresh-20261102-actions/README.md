# Fresh replay and taxonomy receipt, 2 November 2026

The bounded latest-400 refresh completed at 09:54:38 UTC: 350 newly accepted
replays, 50 cached, 361 public GET requests, zero errors or quarantines.
It is not a complete archive synchronization.

Annotation and verification completed at 10:00:25 UTC. The 350 replays contain
24,202 moves and 24,552 referee-validated frames. All annotations have pinned
source replay hashes. Per-team panels retain played version, colour, opponent
version, raw counts and move denominators. The collection includes 331 distinct
complete UCI trajectories; seven trajectory groups contain duplicates, which
must be accounted for when splitting data.

There are 487 queen-capture visibility supplements and 16 en-passant capture
supplements. Queen labels distinguish the victim's decision-time visibility
from visibility immediately before the capture. They do not establish net
material loss or that the victim's move was bad. En-passant supplements preserve
the existing taxonomy definition instead of silently changing historical counts.

`manifest.json`, `taxonomy-summary.json`, and `taxonomy-integrity.json` preserve
the inputs, counts and successful checks. The annotation script's stale reference
to an earlier experiment was corrected before its first execution. Annotation
and verification each completed on their first run. Astra's cores 4–5 were
released afterward.

These records support the proposed action-data development panel. No panel has
yet been selected, no continuation batch launched, and no model fitted from
these records. Belief weights, history tables and king/queen guards are unchanged.
Taxonomy is used to describe and diagnose behaviour; candidate learning and
playing-strength validation remain separate steps.
