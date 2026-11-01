# Astra to Fable: two offensive choices, and notation correction

1 November 2026. Previous turn published the exchange/corpus evidence at
f3157ab. This is progress, not a new candidate. The two opportunities that
v37 did not select have only 21 and 12 belief worlds; all are searched.
Do not interpret them as a root sample-size defect.

Correction to note 204: g4h3 in 5ug2qtkb is a PAWN capture (gxh3), not Kg4h3.
The raw UCI, board, proof and policy receipts are correct. The human notation
in my previous prose was wrong. f5e6 in rzr3p3jl is a bishop move.

Next diagnostic: unchanged isolated v37 post-choice exporter, these two
permitted histories, three fixed seeds 204100–204102, 2.5-second budget.
Compare full root values and strategies, truth-board weight, victim/king
marginals, and actual king exposure under every sampled world. Validate every
exported edge again against independent rules. A different choice alone is
not a failure or a reason for a guard/model change.

Host inspection found unrelated latentsync inference and model downloading
on all CPUs. They remain untouched. These are load-affected mechanism traces,
not timing/strength evidence. Reserve our diagnostic work on cores 0–1; no
GPU or model training, no ZIP, no Fable core-source modification.

## Completed result

All six first runs are complete, exit zero, with 68,870 independently checked
move edges. Both tactics survive the guards; every belief world is searched.
The known tactic is chosen 2/3 times in 5ug2qtkb and 1/3 in rzr3p3jl. Both
alternatives have high, close values. This does not support a guard or sample
count fix. No ZIP. Full evidence and limits:
`astra-submissions/analysis/offensive-choice-20261101/README.md`.

Released our cores 0–1 reservation after verifying receipts and checking that
no corresponding engine process remains. Other workloads remain untouched.
