# v1 — Python prototype (not submitted)

Source: `fog/bot/` in the working repository, not in this one.

## Implemented

Alpha-beta search over a "ghost" belief: the opponent's last-seen pieces carried
forward through fog, with counts capped by what they could still own. Exact legal
moves derived from a single observation. Evaluation with material, placement, a
fog-exposure term for our own king, and an invisible-attack bonus.

## Tried, and what happened

| change | result |
|---|---|
| scouting bonus per newly visible square | **harmful** — 0.792 with, 0.875 without; removed |
| randomised tie-breaking among near-equal moves | regressed 0.875 → 0.667 at the same control |
| pessimistic capturer inference, ghost relocation | ~neutral; two duels disagreed by 2σ |

## Results

0.875 against the course `baseline.py` over 24 games at a shortened control. At
180+2 a later build scored 0W–6L, and the cause was never isolated — the C++
rewrite superseded it first.

## Why it was replaced

44 k nodes/sec capped the search at depth 5–6. More importantly the measurement
was never good enough to tell whether its heuristics helped.

## What carried forward

The exact-legal-move argument, which is the foundation of every later version: a
legal move's destination is always visible, and so is every square a slider
crosses, so filtering on the observation is exact rather than conservative. An
illegal-move forfeit is therefore structurally impossible.
