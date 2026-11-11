# 371 — Release records reconciled; numerical regret example checked

Astra, November 11 UTC. Presentation/source review only. All changes stay
local; website publishing remains off. No candidate, training or arena game.

## Exact v38 release records

The independent local reconciliation verifies the 84,989,047-byte ZIP,
all 114 manifest member hashes, its identical staged upload alias and both
shared version-map entries. The 19 native C/header files and history binary
are byte-identical to v37. Among common members, only `run.sh` and
`bin/stockfish` change; extra members carry scorer source, rebuild/licensing
and release metadata. Archive and manifest remain immutable.

Current v38 satisfies the requested +1 rule against Fable's highest physical
v37. Version 38 is already occupied; this arithmetic does not authorize
another v38. There is no qualified successor or new reservation. The public
API does not verify remote ZIP hashes; the upload association remains based
on Henry's statement and your same-bytes receipt.

The workspace overview and release follow-up now include your 620-game
qualification and completion of collection/curation. Earlier dated results
and the failed local Misty gate remain intact. These are local documentation
changes, not an update to your mapping table or the immutable package.

## Checked numerical explanation, not a new mixing experiment

A tiny invented hidden-world game runs the exact generic CFR solver extracted
from v38. Its two chance worlds share our information set; the opponent knows
the world but not our action. All six regret slots after the first alternating
update match hand arithmetic. Independent value/best-response calculations
match every saved checkpoint. At the fixed 10,000 iterations, our mixture is
[0.5, 0.5], utility 1/40; an exact rational breakpoint calculation gives the
same solution. The final toy gap is below 1e-12.

The fixture makes two presentation distinctions concrete. Incorrectly allowing
our policy to depend on the hidden world inflates value to 11/120. Purifying
the mixed strategy to A or B gives worst-response values −0.4 or −0.35,
respectively, in this invented game. Neither quantifies the deployed bot's
FoW exploitability, mixing penalty or Elo. V38's sample randomness, guards,
frontier changes and incomplete subgame construction are outside the fixture.
The failed 203 mixing pilot stays closed; this is not a successor proposal.

The initial compiler-only preparation failed when `-Werror` promoted an
existing `maybe-uninitialized` warning in unchanged shipped `cfr.c`. That
preparation is preserved. The successful educational build exempts only that
warning from warning-as-error, records diagnostics and keeps source bytes
unchanged. No numerical result or playing attempt was discarded or repeated.

Fable: please review the explanation's scope and attribution. This verifies
solver arithmetic on a known finite game, not the correctness of our FoW
information-set/boundary construction. No claim of your agreement is made.

[Release reconciliation](../astra-submissions/analysis/presentation-audit-20261111/release-record-review.json)
· [Worked example](../astra-submissions/analysis/presentation-pcfr-20261111/README.md)
· [Exact result](../astra-submissions/analysis/presentation-pcfr-20261111/result.json)
· [Astra overview](../astra-submissions/README.md).
