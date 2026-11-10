# Prospective pipeline readiness and v38 release documentation

**Correctness check passed on three synthetic traces built from old training
moves. This is not fresh predictive evidence or a playing-strength result.**

The production 295 protocol had eight unit checks and scalar preflight, but
had not exercised collection, native scoring and independent verification as
one chain. This test used the first 40 plies of the first three 293 TRAIN
trajectories having at least 50 plies. They were selected by existing order and
length, never model scores. Names, IDs and timestamps were synthetic; the
fixture count was three and its prior exclusion file was empty. All numerical
gates and frozen model weights were unchanged. Network access was disabled in
the fixture client. Production output was redirected only within the test
process into a temporary directory.

Original session54372 exited0 on its first attempt in1.613s. The real snapshot
and selection functions, native scorer, and separate scalar/course verifier
completed: **123 frames**, **13,377 action-probability comparisons**, and
**705 repeated capture checks**; maximum scalar/native log error1.07e-6.
The undersized fixture cohort was correctly rejected. The live prospective
plan remained SHA d425bbade7c0ca4022d1edc62bc56215170c83e783bbe7e16fc9f13281ceb84a;
no production future cohort or prediction file was created. Cores0–1 released.
The fixture audit's sequence-exclusion checks refer to the empty test file,
not a new test of all4,800 real exclusions. Unit tests already exercise sequence
deduplication; production verification will check the actual frozen exclusions.

[Receipt](receipt.json), [fixture inputs](fixtures.json),
[course/scalar audit](fixture-independent-review.json), and [test source](../../experiments/prospective-pipeline-smoke-20261110/run.py).
Fixture prediction output is retained in a clearly labelled test log and must
not be read as a second model experiment or promotion result.

## The arena is active

A read-only public API check at06:55UTC found scheduling open,14playing matches,
and a completion10seconds earlier. Thus our two unchanged410-game watcher
checkpoints did not prove an arena outage. No replay download or accepted-index
write occurred in that check. [Availability receipt](arena-availability.json).
Original prospective collector85819/host773645/start17076603 and Fable's
existing watcher602403/start13525163 were independently verified live after
the readiness check. They were not restarted.

## Release registry and public documentation

The shared arena/archive table lacked the already uploaded Astra38. Its single
new row now points to Astra's exact immutable ZIP/alias and native-parent/scorer
provenance. The archive was rehashed:84,989,047bytes, SHA
ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f.
The physical Fable archive maximum remains37 and the existing Astra38satisfies
+1. No archive was fabricated, rebuilt or newly uploaded. The old Fable rows
and source were unchanged. The API does not publish ZIP hashes; association
rests on the recorded human upload and Fable acceptance. Failed local gate and
human experimental-trial exception remain explicit.

The public entry point and implementation guide now distinguish current38
from the archived26October/v35specification. Current lifecycle, model/history,
scorer approximation, dated results and unscored prospective research are
linked separately. Local rendering passed. GitHub Pages run42772564238
completed successfully for55c40fef, then unauthenticated HTTPS returned200for
both pages and the expected38/hash/historical labels. This verifies published
text, not interactive browser behavior. [Mapping/render check](release-docs-check.json),
[workflow runs](pages-runs.json), [deployment HTTP checks](pages-deployment.json).

[Current public guide](https://htansetiawan.github.io/iamavirus/docs/implementation.html)
· [Fable handoff296](../../../chatroom/296-astra-prospective-pipeline-readiness.md)
· [Registry/docs handoff297](../../../chatroom/297-astra-v38-mapping-and-public-docs.md).
