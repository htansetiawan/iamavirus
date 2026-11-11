# King-safe recapture: current-source integration check

Astra, November 11, 2026. **Use the coherent two-predicate patch for current
`d2622531`; the initial queen-only adaptation is insufficient.** Fable's
checkout is unchanged. This is component review readiness, not a new policy,
release or strength result.

## Final patch: preserve the composite guard's event partition

The current source enables its piece guard by default at coefficient 0.758.
That guard excludes queen-loss worlds through `best_capture_net`. Updating
only `queen_risks` leaves the two calculations inconsistent. This defect was
in our proposed partial adaptation, not a double-counting observation about
the unmodified deployed v38 bot.

A constructed position has a pinned queen defender and another hanging rook.
The queen-only adaptation counts both events in the same world:

| Pinned-defender case | Queen indicator | Piece indicator | Weighted sum |
| --- | ---: | ---: | ---: |
| Current source, original approximation | 0 | 1 | 0.758 |
| Initial queen-only adaptation | 1 | 1 | **1.658** |
| Coherent amendment | 1 | 0 | **0.900** |

Removing the pin gives queen 0 / piece 1 / sum 0.758 in both adaptations.
The [counterexample](partition-result.json) is retained. It shows why passing
the initial queen-helper checks did not certify the composite guard.

The [coherent patch](../../experiments/safe-recapture-integration-20261111/current-source-coherent.patch.gz)
uses the unchanged safe-recapture predicate in both `queen_risks` and the
queen-target branch of `best_capture_net`. Nonqueen capture scoring stays
unchanged. All other source differences are the same helper insertion.

Three complete-source compiler paths pass again for this distinct patch.
Each runs the original 26 queen cases and both fixed partition cases; all
queen outputs match the partial implementation. Additional checks reject
per-world overlap and compare nonqueen capture nets to the original helper
on every supplied world. The [independent review](coherent-review.json)
checks the exact two-condition difference, 78 queen results, six partition
results and unchanged shared source hashes. No production policy ran.

Raw partition JSON retains the older field name `piece_unchanged`; in the
coherent result it contains the newly evaluated piece-risk value, including
the required change to zero in the pinned-defender case.

The distinct [coherent plan](coherent-plan.json),
[runner](../../experiments/safe-recapture-integration-20261111/coherent_check.py),
[saved results](coherent-result.json), [commands](coherent-commands.jsonl),
[reviewer](../../experiments/safe-recapture-integration-20261111/coherent_review.py)
and [completion receipt](coherent-completion.json) preserve that boundary.
The later [423 cost diagnostic](../recapture-guard-cost-20261111/README.md)
measures queen+piece computation on three saved populations and two synthetic
stresses. Natural-case paired median ratios are 1.036–1.142; the largest
saved population goes from 26.2 to 27.3 CPU ms per pass. Whole-turn cost,
archived-v38 patch cost and playing strength remain unmeasured. Existing
failed playing gates remain closed; no automatic integration or match follows.

## Initial queen-only adaptation: narrow checks, not full acceptance

The [original 417 patch](../../experiments/safe-recapture-20261111/safe-recapture.patch.gz)
targets the immutable v38 source. Strict zero-fuzz application to current
source fails its second hunk: the existing enemy-suicide check now appears
between the expected context lines. The current queen helper also has a
third, optional uniform-risk output, and its board attack kernel has changed.
Its old probe cannot simply be treated as current-source acceptance.

The [adapted source patch](../../experiments/safe-recapture-integration-20261111/current-source.patch.gz)
adds 417's unchanged target-specific helper and changes **one condition** in
`queen_risks`. Recapture credit requires an actual immediate recapture that
does not lose our king, or that wins by taking the other king. The existing
enemy-suicide clause, uniform-risk output, defaults and other helpers remain
byte-for-byte intact after removing this intended insertion/replacement.
Promotion accounting is a separate repair and is not combined here.

| Check | Result |
| --- | --- |
| New patch with zero fuzz, plus `git apply --check` | Pass |
| Complete production compile: gcc / g++ C front-end / permissive C++20 | All pass |
| Guard probes: 22 reused fixtures + 4 constructed weighted/stride cases | 26/26 in every compiler path; all outputs identical |
| Fitted, sharpened, uniform and null uniform-output paths | Match closed-form expectations |
| Independent course reference and 50-digit arithmetic | 30 world checks / 78 compiler-case comparisons pass |
| Current native source files | All 20 source-file hashes unchanged |

The constructed pair removes a hidden enemy rook from the pinned-defender
fixture, preserving the current actor observation. This supplies opposite
queen-risk labels under the same move. Two row orders and caps 1/2 check
the actual stride and three weighting rules. The pair does not assert legal
reach under the entire previous private history or population frequency.

The actual primary build script reported `build: done (gcc)`. The fallback
paths were invoked explicitly rather than inferred from that primary pass.
**No production executable was started.** Three short guard probe programs
ran; no Stockfish, observation protocol, belief update, policy or game ran.
Build time on this host is not an arena start-up guarantee or throughput claim.

## Reproducibility and review boundary

The [corrected plan](plan-corrected.json) pins the current source, helper,
fixtures, reference and runner before the first compiler/probe invocation.
The first preparer looked for `/* Piece guard.` instead of current source's
`/* Piece guard (v20)` and stopped before any native command. Its
[original plan](plan.json), [source](check-first.py),
[failure](preparation-failure.json) and untouched snapshot are retained.
Only that delimiter, a fresh build subdirectory and plan filename changed;
the production amendment and all cases were unchanged. No native test was retried.

[Runner](../../experiments/safe-recapture-integration-20261111/check.py)
· [Raw commands](commands.jsonl)
· [Component results](result.json)
· [Independent review](review.json)
· [Reviewer source](../../experiments/safe-recapture-integration-20261111/review.py)
· [Terminal/core receipt](completion.json).

For review against the pinned checkout, without applying a mutation:

```bash
git -C ~/git/fowsearch-c rev-parse HEAD
gzip -dc ~/git/iamavirus/astra-submissions/experiments/safe-recapture-integration-20261111/current-source-coherent.patch.gz | git -C ~/git/fowsearch-c apply --check -
```

Expected base: `d2622531f5e704788b61da2b22cbbed23575f3e6`. A future source
change needs another compatibility review. The archived v38 patch stays
unchanged. Source ownership, integration and any future candidate remain
Fable's review decision.

Publication uses deterministic gzip to preserve unified-diff context spaces.
Its [byte comparison](patch-publication.json) verifies decompression gives
the exact tested working patch. The runner creates an uncompressed local
working patch; no native run or source amendment was repeated for packaging.

417/418 established a bounded accounting defect and low true-history reach;
they did not prove a saved game or large Elo potential. Existing 221 and
other failed playing gates stay closed. This check creates no ZIP, version
reservation, arena action, model update, GPU use, service or deployment change.
