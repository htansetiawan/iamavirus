# Duck v11 midgame capture belief diagnostic

The v38 replay harness emits its decision before reading the recorded capture
labels. The added C readout measures weighted attacker occupancy and the
specific available capture across the full retained belief. The audit joins
those figures with attacker occupancy in the solver sample and the retained
alternatives identified by the earlier true-board analysis.

[Plan summary](plan-summary.json) · [C/C++ preflight](preflight.json) · [Result](result.json)
· [Verification](terminal-verification.json).
