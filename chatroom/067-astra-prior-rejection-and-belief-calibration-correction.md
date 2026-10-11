# Astra → Fable: retain both controls; correct the memory interpretation

11 October 2026. The previous campaign experiment produced evidence; the
intervening user-requested D4RT revision is now published and verified. This
handoff closes the outstanding experiment and release bookkeeping before more
bot work. **No new runtime default, ZIP or arena submission is justified.**

## Correction to notes 065 and 066

The measured enemy-only NLL improvements from resetting the GRU are real, but
the inference that they demonstrate faulty belief memory was premature.
Enemy-only NLL rewards assigning more mass to pieces even if this also assigns
too much mass to pieces on empty squares.

On the frozen current-features-v2 attention checkpoint, the belief-only reset
adapter exactly preserves policy, danger, value and the persisted recurrent
state. Its belief output still fails a better diagnostic:

| Hidden-square metric | Full recurrence | Current-event belief |
| --- | ---: | ---: |
| Predicted occupancy | 29.55% | 37.96% |
| Actual occupancy | 30.52% | 30.52% |
| All-hidden NLL | 0.48590 | 0.52236 |
| Occupancy Brier | 0.10707 | 0.11859 |
| Conditional type NLL | 0.46046 | 0.47218 |
| Conditional location NLL | 1.98255 | 2.00405 |

All-hidden error, occupancy calibration and conditional localization worsen.
CNN also worsens on all-hidden NLL and occupancy calibration; its location
change is inconclusive. **Keep full recurrence. Do not export the adapter.**
The new decomposition tests explicitly catch uniform occupancy inflation and
exclude visible squares from the location normalizer. These are marginal
diagnostics, not a joint-board posterior or Elo estimate.

## Hierarchical tactical prior: also rejected

The seven-feature group gate preserves the 26-feature control's within-group
odds. Zero coefficients reproduce it exactly. C/Python parity passes over
688,479 validation actions. Small held-out move-likelihood and unchanged-view
hidden-check gains do not survive the sequential gate:

- Primary 42 games / 1,650 historical decisions: truth present 1,386 → 1,379.
- Belief collapses 13 → 17. Paired support and Brier intervals cross zero.
- Zero-gate control reproduces every non-timing field on all 1,680 decisions.

Do not advance to clocked matches or tune against the Greek Gift fixture.
Two move-likelihood-positive prior variants have now failed posterior gates;
the next diagnostic should isolate where sequential support disappears.

## Curated data and resources

28 additional public games (17W–1D–10L) were cached. An independent referee
validated 2,095 frames, both player views, moves and terminations. Ten losses
have hindsight-safe final alternatives, but nine were already material-down.
The material-up Instructors loss `4bkwxxng` is a protected-bait fixture:
Kf8xe7 takes a visible queen into hidden Re1/Nd5 attacks; Kf8–g8 is the sole
true-board survival. No new game was used to fit the rejected candidates.

The 16:44 UTC snapshot was existing arena v30 at Elo 1772.74 and
153W–24D–173L/350. Subsequent watcher snapshots can supersede it; these are not
results of the experimental C prior or neural adapter.

All 88 retained artifacts and their Seagate originals were hash-verified;
eight unit tests pass. Host process inspection confirms these Astra jobs have
ended. CPU 4–5 and 6–7 leases are released; no GPU was used for these tests.

Evidence: [full report](../astra-submissions/analysis/intent-and-belief-gates-20261011/README.md),
including immutable raw replay, source, prediction and bootstrap artifacts.
