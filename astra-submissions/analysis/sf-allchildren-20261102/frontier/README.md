# Native search-frontier fidelity/cost gate: pass

The unchanged one-pass scorer passes on 256 sampled search parents (32 per
each of eight previous cost decisions). They were selected by FEN hash from
22,635 native Stockfish submissions, independently of scoring and outcomes.
Three unsupported/fewer-than-two-legal parents were recorded and excluded
before scoring. Referee/private-input audit covers 273 frames and all eight
actor histories. Capture-only logging changes the explored workload; this is
not an exact-work tree comparison.

| Metric | Cold | Warmed stream |
|---|---:|---:|
| Speed vs shipped Stockfish | 1.694x | 1.993x |
| Speed vs same-build base | 1.725x | 1.987x |
| Mean absolute value error | 0.01387 | 0.03613 |
| Reference-value best-action regret | 0.00024 | 0.01498 |
| Regret >0.5 | 0 / 256 | 1 / 256 |
| Exact top-choice agreement | 254 / 256 | 190 / 256 |
| Mate-label/sign disagreements | 0 | 0 |

All frozen gates pass. All 6,144 first-attempt queries complete, collector
28711 exit 0. Review checks 202,560 scored moves, 3,072 control pairs and
complete move coverage; shipped/base/off outputs match, repeats match.

The warmed disagreement is material: case 465co8me-26:c208080689e1 chooses
f8c8 instead of a5a4, with reference regret 0.50298 and 108 nodes instead of
2,885. This is an approximation saving search work, not simply faster execution
of identical scoring. One other case has regret 0.42998. No window or threshold
is tuned from these results. These are reference scores, not FoW truth.

The candidate advances to a separately frozen equal-clock native decision
screen with fresh scorer workers for each arm and identical beliefs, masks and
world samples. No new ZIP, arena action, GPU use, or Elo claim.
