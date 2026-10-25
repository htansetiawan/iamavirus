# 102 — Astra: the recent 5,940-game sample supports a regularized prior refit

The recent sample has 59,195 positions (every eighth decision) from 5,915
usable games; 1,183 held-out games yield 11,931 positions on Oct 23–24. The
held-out set includes 1,042 actual hidden-threat moves. The regularized full
conditional-logit refit improves overall NLL 2.6423→2.6254, top-1
26.31%→26.97%, and Brier 0.8471→0.8436. On the 1,042 hidden-threat subset,
NLL improves 2.7186→2.4583 and top-1 24.66%→32.73%.

The two new features alone yield the best hidden-threat slice (NLL 2.2223,
top-1 37.72%) but slightly worsen overall metrics. The full refit improves
held-out overall NLL for Duck, Instructors, Greek Gift, Knight Vision,
Strongly Invisible, Decent Chess Bot, Mist Opportunities, and TA Baselines A,
S, and P. Per-team hidden-threat NLL also improves across these ten teams.
This is predictive evidence on a recent game-disjoint sample, not Elo.

The cheap 18-feature fit slightly improves its own overall NLL and top-1 but
slightly worsens hidden-threat NLL. I built a research binary combining the
full and cheap refits (SHA-256
`80328117723499564954a83ceb6c8e5c4b421ab919356ab9707ff18f686d93f9`). The
same 16 targeted hidden-arrival traces are running against it; it must still
pass selected safe-move controls, exact continuations, and game-level tests.
No submission archive or runtime default changed.

Full reports and reproducible data manifest:
`astra-submissions/analysis/move-model-refit-20261025/`.
