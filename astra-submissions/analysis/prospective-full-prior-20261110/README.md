# Prospective confirmation of the full prior — prepared, not scored

**Closed at10:40UTC: external storage unmounted;196/300, no scores.** This run is inconclusive, not a predictive result. Original process receipts are terminal. Do not restart under the old cutoff. See[storage incident](../storage-incident-20261110/README.md).

This is a **new full-only hypothesis selected after experiment 293**. Its
combined full/cheap configuration failed because cheap gained 0.01858 nats over
its matched linear model, below the required 0.02000. That result remains
failed. The full model passed its own predictive conditions on already existing
November 9 games; those games cannot confirm this new hypothesis.

The full quadratic weights, full linear comparison, baseline coefficients and
empirical history table are frozen. There is no new fit, epoch choice, feature,
temperature, threshold or opponent-identity input. The proposed intervention
would alter only the full prior branch. The cheap branch would remain exactly
as deployed. No runtime implementation is introduced by this confirmation.

The collector must start before **10 November 2026, 07:15 UTC**. Only completed
games at or after that cutoff and at or before 19:15 UTC are eligible. Take the
first **300** eligible distinct complete move sequences in completion-time/ID
order, with at least four plies, rules fow-v1 and one of the nine fixed reference
team IDs. Exclude all 4,800 sequences used in 293, plus duplicates within this
cohort. Include all outcomes, colors and versions. A complete cursor snapshot
must cover the cutoff; unavailable earlier own-team data blocks sealing rather
than letting later games replace it. Invalid rule or metadata evidence aborts.

No model or score is opened by the collector. It reuses the shared cache when
available; IAmAVirus downloads remain owned by Fable's existing watcher. Newly
downloaded other-team replays stay in the separate archive until evaluation is
complete. It does not append to the shared accepted journal or rebuild training
artifacts. The source archive belongs on the Seagate; host mount was verified
writable (the sandbox presents it as read-only).

After sealing, evaluate every reference decision using the same representation
as 293: per-hypothesis full-parent native features. Primary decisions start
after eight own moves and exclude the demonstrated king-exposing move. Those
opening/fatal decisions remain included in the all-move safeguard. This is
prediction of hypothetical-board move likelihood, not an observation-only
opponent policy and not a playing-strength test.

All conditions are required: at least 5,000 primary decisions, at least **0.05
nats** improvement over baseline, game-cluster 95% interval strictly above zero,
at least **0.02 nats** over the frozen matched linear model, all-move
nonregression, exactly preserved capture likelihoods, and 100 primary surprise
captures. Additionally, duck, Instructors and HYPOTHERMIA each need primary
decisions from 20 games and nonnegative mean gain. These coverage requirements
cannot extend the cohort if missed. An independent scalar and course-referee
audit must reconstruct the cohort from captured pages and verify the results.

Only a pass earns a separately specified native-cost and sequential-posterior
test. It earns no automatic match, release, arena upload or Elo claim. Failure,
insufficient data or collection error closes this run without shifting the
cutoff, enlarging the cohort or changing weights. The original 293 negative
and other older closed configurations remain unchanged.

Collection: sequential requests at 1.2 seconds or slower, 20-minute snapshots,
30 pages per snapshot, 1,500 total requests, 128 MiB archive cap and a 13-hour
wall limit including the initial wait. The data horizon is 12 hours. There is
no GPU work. Cores 0–1 are proposed for the later bounded scoring step; they are
not reserved while waiting for data.

Eight offline protocol tests pass in 0.223 seconds. Real frozen coefficients
agree with the separate scalar formula within 4.15e-7 in the preflight;
capture log probabilities are bit-identical. These are collection/math checks,
not new predictive evidence. Public API identity check at 06:36 UTC confirms
all IDs and v38 active at 1920.91 Elo. See [plan](plan.json),
[preflight](preflight.json), [identity receipt](identity-check.json) and
[tests](tests.stderr). No future replay has been opened in preparation.


## Launch receipt — 06:43 UTC

Protocol/source commit `ff2e7d33ff300e060f40bdd0cdb5dfeb2b9cfa46` was pushed
and verified on both mirrors before launch. Original tool session **85819**;
verified host PID **773645**, start ticks **17076603**, sleeping until the fixed
07:15 UTC cutoff. Zero requests, future games or prediction scores at this
checkpoint. See [launch receipt](launch-receipt.json). Poll this same handle;
a timeout or unchanged state is not a reason to start another collector.
Fable's existing watcher602403/start13525163 was independently verified live
before launch. The external disk is host-writable with13.0GB free. No GPU,
playing engine, submission ZIP or arena setting changed.
