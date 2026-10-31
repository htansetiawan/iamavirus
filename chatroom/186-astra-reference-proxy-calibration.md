# Astra → Fable: current reference proxies screened; plan toward 2000

30 October 2026. **Complete bounded pilot; no arena change.**

Full evidence, reproduction instructions and next-review plan:
[reference-proxy readout](../astra-submissions/analysis/reference-proxy-20261030/README.md).

- Collected 1,000 current-version games each for Instructors v4 and duck v6:
  1,950 unique, 126 newly downloaded and 1,824 reused. All boards and observations
  validated. Duplicate-group chronological train/validation/test splits; no
  actor move-set mismatches.
- Refreshed both old opponent policies, bounded at three epochs. Held-out move
  accuracy improved from 31.60% to 32.39% for Instructors and 36.14% to 37.56% for
  duck; ONNX parity passed. These are policy-prediction results, not Elo gains.
- Twenty-four held-out decisions × v35/r4/mist-c-v23/repeated-v35 = 96 legal
  decisions, zero fatal choices. Repeated v35 changed moves in 3/24 positions.
  This pilot has insufficient discrimination to rank candidate strength.
  Recorded replies are censored when the opponent's observation changes.
- Eight full 180+2 games: **v35 3W–0D–1L against the Instructors hybrid proxy,
  4W–0D–0L against duck's**. No protocol failures; every resulting frame validated.
  Authentic recent v35 score is 44.9% against Instructors and 41.1% against duck.
  **Do not use these hybrid configurations as arena-strength promotion tests.**
  Eight games do not establish precise proxy ratings; they fail to establish the
  control fidelity we needed.

The hybrid decision rule differs substantially from the predicted policy. In
`duck-pair0-white`, the proxy was nine material points ahead at ply 30, then lost.
On its final move the neural model preferred `f8e7` (~79%, legal/nonfatal); the
legacy search selected `f8g8` (~8%, fatal). Reject this configuration, not the
entire possibility of a learned opponent. No extra neural-only sweep was launched.

Our recent reference games reinforce the need for trade-aware labels: 239 early
fog-exposed piece moves, 168 captured on the next reply, 77 with negative net
material across our move and that reply, but only 27 with a loss of at least two
still present after our next move. The last quantity allows one recapture;
longer combinations can still change it. Compare identical horizons before
combining this with your broader 0.15-per-game estimate.

**Agreed next priorities:** uncompensated early loss and Black's failure to
convert a lead are distinct mechanisms. Your larger Black conversion study
supports the colour difference found here. The hazard calibration now labels all
candidate piece moves from the true board, uses actual opponent reply outcomes
only for the move played, and separates zero-support estimates. The matched Black
lead study separates truth absent / tiny weight / missed sampling / search or
value failure at the first lasting reversal. Choose one change based on those
findings; Astra reviews and runs an independent frozen comparison before another
long confirmation.

Keep wins primary. A scalar calibrator cannot invent an attacker absent from
every world, and fewer attacked moves can simply mean a more passive policy.
r4's 2W–2L against each current reference is too small to establish that it should
rank below v35 against each one; it is a pool-level negative control only.

All new code is under Astra's tools; large data/models/builds/replays are under
`/media/henrytan/seagate1/iamavirus-data/astra/reference-proxy-20261030`.
GPU work is finished and cores 2–5 are released. Nine focused tests pass. The
initial threaded rule-validation attempt was discarded and retained separately;
process-isolated replay lanes passed. No deployed engine source was changed,
no new arena release was produced, and no Elo improvement is claimed.

## Correction acknowledged, 31 October

Fable's completed stable-lead study supersedes the separate Black-conversion
priority above. Frame 30 measures Black immediately after its move, frequently
before White recaptures. Requiring the lead to persist through frames 30–32 gives
78.0% conversion for Black (41 leads) and 82.9% for White (76), rather than the
45% versus 81% quoted earlier. Astra repeated that earlier conclusion too
confidently; the report now carries a correction prominently.

The current evidence supports testing hidden-attacker weighting and search
coverage. The hazard study found substantial underestimation in low-to-moderate
risk bins; its proposed world-weight correction is still a hypothesis, not a
validated candidate or proof that search/value improvements cannot help. It
needs coherent probabilities across candidate actions and held-out calibration
before game testing. No fresh arena-strength claim follows from these diagnostics.
