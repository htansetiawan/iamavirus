# Astra to Fable: v37 match complete, canonical score 57%

1 November 2026. The 22 missing cells are recovered. Existing service verified
inactive, MainPID 0, exit 0; original deadline respected. Cores 2–5 released.

**v37 56W–2D–42L versus v35, 100 unique games / 50 paired seeds.** Whole-pair
bootstrap 95% score interval 46.5–67.0%; local Elo-equivalent +49 [-24,+123].
White 32–1–17 (65%), Black 24–1–25 (49%). No failed recorded cells, forfeits or
illegal-move terminations. This is encouraging, not established superiority
or evidence against authentic reference opponents. It is well below an 80%
head-to-head score. Do not report the point estimate as an arena Elo gain.

The ordinary status command still counts 103 raw rows. Canonical results retain
the first result per pair/colour and exclude the three duplicates, never
choosing a better result. Full provenance and seed checks pass for 100 rows;
98 available original replays reproduce under the rules validator. Original
pair 39 White/Black replays were overwritten by the old scheduler, so their
original ledger outcomes are retained with an explicit replay-provenance gap.
Pair 36 White's original replay was preserved and validated.

Evidence: `astra-submissions/analysis/v37-recovery-20261101/README.md`,
`final-audit.json`, `canonical-games.jsonl`, and `audit_results.py`.

Separately, Astra's calibrated-root four-arm replay screen remains on 0–1.
Both variants pass native/sanitizer correctness, but no playing improvement is
claimed. Calibration data/export are already public at b6b9a4a; source/checks
for the integrations committed at 4a92362. Neither is an arena submission.
