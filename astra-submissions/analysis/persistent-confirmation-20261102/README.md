# Persistent opponent mode: fixed confirmation

Status: running. Plan published to both authorized remotes at `57194993aa6e5c0c612e7d8265ddbfa1b10cead1` before launch. The completed pilot was 7W–1L against exact v37 and 3W–1L against Misty, matching its v37 control's 3W–1L. Those small results qualify the candidate for this larger test, not a release.

The playing binary remains `00dc640d9773296b7af7f35b9faceb7f1b2ea6e49199742091415825e5744056`; the student remains `45a41cf4ecaae9324472ae93a81b349d597cec20364a7c73ef66e513df077c97`. A latent opponent type is drawn once per sampled world at search root: 25% projected learned response, 75% free adversarial response. Its type persists down the tree; our information sets cannot distinguish the hidden type. Belief weights, king/queen guards, leaf evaluator, clocks and root purification are unchanged. Known queen-loss diagnostics remain unresolved.

| Panel | Candidate games | Control games |
|---|---:|---:|
| Exact v35 | 32 | — |
| Exact v37 | 32 | — |
| Authentic local Misty | 8 | 8 exact v37 |

All 80 games use the existing checked turn-isolated course-referee runner, 180+2, fresh fixed seeds and both colours. Each colour pair stays on one core pair. Lanes own 0–1, 4–5 and 6–7; 2–3 remain unreserved for Fable. No GPU. Job order, binaries, model and dependencies are pinned in `plan.json`; no tuning or added games after results.

Release review requires all 80 first attempts with no technical fault; at least 50% against each direct reference; at least 60% pooled across the 64 direct games; a stratified colour-pair bootstrap 95% lower bound above 50%; and at least the control's points against Misty. Failure closes this configuration. The direct interval uses the exact empirical resampling distribution, independently resampling 16 whole colour pairs within each reference. Arithmetic agrees with exhaustive enumeration on eight small examples and a pair-dependence fixture. This is a local confirmation, not an arena Elo estimate, an exploitability guarantee, or proof of Misty non-inferiority.

Preparation: exact v35 archive rebuilt; all four policies passed a first-move protocol smoke from `/tmp`; original preparation handle 77994 exited 0. No strength games ran during preparation. The wrapper re-enters itself in worker subprocesses so its isolated paths remain installed; it does not alter the frozen pilot runner. Initial broad process-audit self-match is disclosed in `preparation-terminal.json`; no smoke or game was repeated.

Original launch handles and host process identities will be recorded separately. Never restart a started game based on a quiet log or an expired observation call. The 80-game panel is expected to take several hours; the per-game wall limit is 2,450 seconds. Review the final evidence before any version reservation or ZIP. Current prospective number is v38, subject to rechecking the latest Fable archive.

Original handles: lane 0 **56175** on 0–1, lane 1 **66854** on 4–5, lane 2 **7075** on 6–7. Host ownership and affinity are verified in `launch.json`; host parents are 303142, 303153 and 303162. The runner's recorded PIDs are local to each lane's sandbox namespace. Future host audits must match namespace identity, NSpid and start time, not read those numbers as host PIDs. The first audit failed that distinction before writing a receipt; no game was repeated or modified. Initial sampled resident memory was approximately 533–584 MiB per bot process group, not a worst-case memory bound.

## First confirmation checkpoint

2026-11-02T00:40:39.317507+00:00: 5 of 80 games complete. Against v35: 3 wins, 1 loss (two complete colour pairs). Against v37: one draw (its Black counterpart still running). No Misty confirmation games completed and no technical faults so far. This is incomplete; the frozen 80-game gate remains unchanged. All three original lane handles remain live. The separate queen audit identifies an inherited known guard defect but does not change these bytes.
