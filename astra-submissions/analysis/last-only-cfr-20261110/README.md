# Last-iterate-only CFR specialization — November 10

Completed: original12142exits0 at20:12:26UTC after2.35s. Correctness only;
no measured speedup or strength claim.

Reuses the253/254cached/selective solver; its old whole-search speed gate failed.
The separate new compile-time mode omits the unconsumed average buffer and
scan. Default builds retain exact average sums/API; last-only builds explicitly
reject average API use, includingNDEBUG. Current v38 consumers use last iterate.

Four original-vs-optimized synthetic/growing comparisons cover default/last-only
and optimized/sanitized builds. Require9569checkpoints and8193updates each;
last-only comparisons exclude the intentional dummy average quarter, leaving
4,697,454meaningful regret/prediction/current doubles per comparator. Two
NDEBUG average-API calls check default success and last-only explicit refusal.
No actual timing mode is launched, despite reused harness support for one.

One generated newline compilation error was fixed before the run; original
preparation logs remain. Six bounded calls,exclusive cores4–5,600seconds total,
no API/GPU/model/arena or original-collector changes. Source/42pins publish
before correctness execution. A separate current-v38 cost design is required
before any performance or game conclusion.

[Scope and nearest prior](../../../chatroom/330-astra-last-only-cfr-correctness.md) ·
[plan](plan.json) · [build](build.json) ·
[reproducer and full copied C sources](../../experiments/last-only-cfr-20261110/).

## Complete result

All four exact comparisons pass:9569checkpoints/8193updates each, including
496stale prediction clears. Default builds compare6,263,272state doubles and
exercise average-policy outputs. Last-only builds compare4,697,454meaningful
regret/prediction/current doubles and assert the average buffer is absent.
Native and address/undefined/leak sanitizer results agree. Both NDEBUG API
fixtures behave as required: default succeeds, last-only explicitly aborts.
The separate review confirms all42pins, ten consumer-source files and
unchanged teacher/metadata pins. Cores4–5released.

[Raw execution](execution.json) · [independent review](independent-review.json) ·
[terminal receipt](terminal-verification.json). Source2f0cf8d2was verified on
both mirrors before execution. No timing mode or real-game test was run.
The old254advancement failure remains failed. A distinct current-v38 cost
contract must compare original/cached/last-only arms with within-case order
balancing and identical belief/guard/world inputs before choosing any pilot.
