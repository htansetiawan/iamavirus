# November 11 presentation inventory

Henry's current priority is understanding the implementation for December 3.
The audit reads the immutable v38 ZIP and its manifest. It runs no bot,
training job, external request or match.

All 114 manifest member hashes match; the ZIP has 115 members. Its empirical
table contains 359,889 unique history/move records across 219,137 distinct
64-bit history keys. The file is 5,758,240 bytes, including a 16-byte header.
Both move-model vectors contain 28 coefficients: 25 nonzero in the full
vector and 17 in the cheap vector. The source records a 148,357-game fit;
this audit does not reconstruct that training population.

The generic solver has four allocated per-information-set/action arrays.
Their entries vary with the current tree; these are not four offline-trained
models. Current move selection uses last-iterate argmax, and the tree is
freed after every decision. Model weights and history counts are frozen.

```bash
.venv/bin/python astra-submissions/tools/audit_v38_presentation.py
```

[Inventory](inventory.json) · [Audit source](../../tools/audit_v38_presentation.py)
· [Human overview](../../../docs/presentation-20261203.md)
· [Tables and algorithms](../../../docs/presentation-tables.md)
· [Experiments](../../../docs/presentation-experiments.md).

The public API cannot verify the uploaded ZIP hash. The recorded archive/arena
association comes from the human upload and registry. Counts are structural
facts about that artifact, not playing-strength or equilibrium guarantees.

## Selected replay illustrations

[Case provenance](case-illustrations.json) pins the two already-audited replay
fixtures and generated SVGs. [The generator](../../tools/illustrate_presentation_cases.py)
uses recorded private views, exports two selected snapshots and runs no bot.
The [walkthrough](../../../docs/presentation-cases.md) distinguishes the arena
v38 win from the rejected experimental candidate's local loss.

## Information keys and data lineage

[Source/count review](information-review.json) checks the four core archived
files against their parent commit and records the actual information-set
reuse check. It also distinguishes loaded history records from the subset
meeting the runtime count floor. The [human reference](../../../docs/presentation-tables.md)
now explains the data-to-coefficients/counts path and which parameters can
change at runtime. The old streamed-fit population remains source-recorded:
the exact fitting command/dataset has not been reconstructed by this audit.
