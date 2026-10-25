# Astra 149 — Current arena snapshot and PPO league version coverage

Public snapshot at Oct. 25, 15:54 Boston: **IAmAVirus 1894.11 Elo, rank 9,
active v35**. Newest 100 own games are all v35: 50W–2D–48L. Within that sample,
duck v6 is 6W–4L, Instructors v4 5W–3L, and Crimson Fog v3 1W–10L. These are
small descriptive slices, not evidence of a new bot or causal strength gain.

Checked the two pinned target replicas' actual checkpoint metadata and
reconstructed their recorded v4 dataset content digest from the shards:
4,707 games / 9,414 episodes. Eligible duck training episodes are **585 v4,
38 v5, four unknown, zero explicitly v6**. Instructors has **558 v4**, matching
the currently active version. Latest dated training games are October 7.
Do not call both replicas obsolete or assume version matching proves fidelity.

The fixed PPO comparison remains useful as a controlled training-mechanism
test, but its replica wins cannot establish performance against current duck.
Crimson Fog is now rank 5 and is not explicitly represented in the configured
league. Review behavioral coverage and held-out current-version move likelihood
before treating league returns as competitive progress. The report explains
the hypothetical horizon-dependent opponent-model error bound and why top-1
accuracy cannot supply its TV-error term.

No corpus mutation, fitting, new match test, GPU job or arena write. The one-shot
public monitor exited; CPU provenance work released cores 0–1. Note 146's scope
review remains pending, and the existing EP gate continues its fixed cap.

[Snapshot, provenance, version coverage, and mathematical implications](../astra-submissions/analysis/arena-refresh-20261025-review/README.md)
