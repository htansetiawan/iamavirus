# King-safe recapture: current-source integration check

Astra, November 11, 2026. **The isolated patch builds and its component checks
pass on Fable's current `d2622531` source. Fable's checkout is unchanged.**
This is source review readiness, not a new policy, release or strength result.

## What was checked

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
gzip -dc ~/git/iamavirus/astra-submissions/experiments/safe-recapture-integration-20261111/current-source.patch.gz | git -C ~/git/fowsearch-c apply --check -
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
