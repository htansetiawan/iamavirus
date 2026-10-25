# Independent audit of hidden king-attack labels

2026-10-25. Fixed sample of 512 games, seed 20261025, from the existing
123,251-game top-name-filtered corpus. This checks the saved census against the
independent Python referee. It is not a new bot experiment or an Elo estimate.

All **512 games, 40,348 frames and 1,336 newly created attack events** pass.
That includes **80,696 attacker-set comparisons**, legal replay reconstruction,
both players' observations, and agreement between independently derived events,
the current scanner and the previously saved compressed census. One older
`source: corpus` replay lacks clock metadata; board/observation validation does
not use clocks. Its provenance is recorded rather than silently excluding it.

The audit also enumerates the defender's pseudo-legal replies and marks those
that avoid immediate king loss. Results restricted to events with a recorded
reply **and at least one safe alternative**:

| Attacking pieces' visibility to defender | Immediate loss after recorded reply | Rate |
|---|---:|---:|
| Fully hidden | 166 / 528 | 31.44% |
| Visible | 62 / 682 | 9.09% |

The difference is **22.35 percentage points**, with an approximate
game-clustered 95% interval of **17.95–26.74 points**. There were also 43 hidden
and 42 visible answered attacks without any king-saving reply; those are
excluded from the table. Mixed-visibility attacks are tracked separately.
Events without a recorded reply do not count as successful attacks.

This rules out “all these victims had no escape” as an explanation of the
observed gap. It does not establish a causal effect of concealment: opponent
strength, available moves and position difficulty still differ. Safe here means
surviving this move, not having a winning continuation. These remain offline
truth labels, never observations the live actor may receive.

## Frozen teacher-readiness panel

`teacher-readiness-panel.json` contains **80 positions from 80 distinct games**:

- 16 hidden attacks where an available escape was missed.
- 16 visible attacks where an available escape was missed.
- 16 hidden attacks successfully escaped.
- 16 visible attacks successfully escaped.
- 16 ordinary controls with no current attack on the moving side's king.

Selection uses a fixed hash order within each slice and no repeated game. The
panel uses complete-clock replays so the existing actor-prefix driver can read
them directly. Every replay hash and prefix boundary is frozen. Slice labels
and safe-reply lists are for the evaluator only. The bot input consists solely
of the side's observation stream and its prior own moves.

This is a **diagnostic panel**, not a guaranteed clean holdout: earlier fitted
models may have seen these historical games. It is balanced by construction,
so its aggregate failure rate does not estimate the arena's failure rate.
Its purpose is a fast, reproducible check that a proposed stronger teacher
actually improves decisions across several patterns. A release still needs
independent held-out data and games under the deployed controller.

## Artifacts and reproduction

- `sample-manifest.json`: exact selected games, hashes and metadata.
- `events.jsonl.gz`: independent event labels and all immediate safe replies.
- `summary.json`: counts, uncertainty calculation and provenance hashes.
- `teacher-readiness-panel.json`: fixed diagnostic cases.

The validator is `../validate_hidden_attack_census.py`. The original selection
was made with:

```sh
taskset -c 0 /home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/analysis/hidden-slider-zone-20261025/validate_hidden_attack_census.py \
  --path-list /tmp/iamavirus-top-replays.txt \
  --referee-dir /home/henrytan/git/fow-starter \
  --census astra-submissions/analysis/hidden-slider-zone-20261025/top-opponents-hidden-king-arrivals.jsonl.gz \
  --out-dir astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512
```

If the original temporary population list is unavailable, the committed sample
manifest retains all 512 selected paths and hashes. A path list made from those
entries permits revalidation of the same games (but is a sample-only input,
not a reconstruction of the original population selection). Reserve the CPU
core in `chatroom/cores.json` before rerunning.
