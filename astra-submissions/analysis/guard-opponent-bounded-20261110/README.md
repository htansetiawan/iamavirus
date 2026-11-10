# Guard comparison closed: no promotion

Original session **65095 exited 0** after 23 first attempts: 22 normal games,
one opponent exception and nine unstarted jobs. The all-clean/full-32 gate
fails. This queue is not resumed and these candidate bytes are not promoted.

The independent course audit checks **1,916 frames**, source/result hashes,
move legality, both observations, clocks, outcomes, paired seeds, process
controls and population-cap telemetry. Host cleanup finds no owned actors.

The raw all-attempt receipt records candidate 8/12 points and control 10/11.
One candidate win came from Misty exiting after its own Qa4. Excluding that
fault leaves **ten complete clean matched cells: candidate 6, control 9**.
The incomplete scores are unfavorable; they do not prove an arena Elo gap.
The original native 10.5/16 pilot remains a separate result, not pooled here.

The comparator used Brian Liou's local Misty 0.1.3/v1.6 profile with Rust,
a live clock manager, 200,000-state cap, telemetry and off-turn freezing.
Two prior score-independent health games passed, including real cap events.
That did not establish universal runtime reliability: in this panel the cap
left no state consistent with a newly revealed own-move observation.
A separate component trace reproduces the capped exception while uncapped
updates finish. No fourth comparison or package change is automatic.

All started attempts are retained; none is replaced or discarded. Source
and queue were published at 38ccde76 before launch. The declared gate and
seeds stayed unchanged. Independent audit and cleanup are terminal receipts.

See [audit.json](audit.json), [completion.json](completion.json),
[cleanup.json](cleanup.json), [the cap diagnostic](../misty-empty-belief-20261110/README.md)
and [the full root census](../root-population-20261110/README.md).
