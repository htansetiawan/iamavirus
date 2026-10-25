# Astra 144 — Native risk-label gate passes; old-head failure survives overlap exclusion

The optional PPO patch from note 143 now has independent native-label evidence.
On 80 real replay prefixes, **163,946 candidate labels across 5,279 positions**
match the external referee, with zero board/observation/candidate/termination
mismatches. Coverage includes 456 castling, 212 promotion and 7 en-passant
candidates. The isolated build took 14.87 seconds; full check 22.27 seconds;
native danger queries alone 0.0623 seconds. This supports using the existing
`BatchEnv.danger()` API; it is not training throughput or strength evidence.

I also verified the old attention model's frozen training manifest and shard
hashes at the new disk mount. Four of the 80 diagnostic games occur in its
recorded training set. Among the remaining 76, with neither game-ID nor complete
move-sequence overlap with recorded training/selected-validation games, the
unrestricted minimum-risk head is fatal 36 times versus v35's 9. Current-root
reranking gives 7. The failure remains after removing known training overlap;
these are still selected historical cases, not population calibration data.

This closes the specific native-label prerequisite. Please review the ready
PPO patch and bounded training proposal in note 143; no further heuristic sweep
is proposed. No GPU job or new tournament started. The existing fixed-cap gates
remain in flight (last read: EP 8.5/17, tighter guard 14/34), without promotion.

[Report, code and raw evidence](../astra-submissions/analysis/deeprl-table-audit-20261025/native-risk-readiness.md)
