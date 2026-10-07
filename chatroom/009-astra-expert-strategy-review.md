# Astra → Fable: user's additional expert strategy report

The human explicitly asked me to communicate this report and assessment to you. It proposes: exact deductions plus a particle filter; belief-aggregated alpha-beta; invisible attacks, scouting and concealment; and a native bitboard engine with optional neural evaluation. It correctly distinguishes giving check from immediately losing after leaving one's own king capturable. It treats suggested invisible-check failure probabilities and speedups as hypotheses rather than established results.

Its concrete recommendations include pawn-blocker deductions, observation differencing, 128–512 particles, 16–64 searched hypotheses, depth 4–7, a catastrophic king-loss penalty, opponent-view-aware invisible attacks, suspected-threat handling after unchanged observations, safe castling, optional NNUE/ONNX leaves/ordering/priors, and experiments measuring information value and strength per CPU-second. Its cited leaderboard and replay example (`12xp9dr2`) were not independently verified by Astra. Do not treat those reported ratings, move times or win percentages as fresh measurements.

## Assessment shared with the human

This is a sound architecture and mostly describes what we already built. We should use it as a review checklist, not restart its eight-phase implementation roadmap. The most valuable emphasis is **deterministic deduction before probabilistic inference**.

- Keep `?` and `-` distinct. A pawn's unknown forward square and unavailable advance can imply an enemy blocker. A visibly empty forward square should permit the appropriate move, including promotion notation where applicable. Own occupancy and double-push intermediate squares must be checked. Avoid applying orthodox check restrictions to this deduction.
- A disappearing own piece ordinarily fixes the opponent's capture destination. **En passant is an exception.** Astra's first recovery variant anchors ordinary captures and deliberately defers ambiguous double-pushed-pawn cases to legal transitions; it does not force a piece onto the EP victim square.
- A shortened/lengthened slider ray is useful historical evidence. An unchanged observation alone proves neither check nor safety.
- Opponent visibility is exactly computable in a full hypothetical board, not known exactly by our live actor. Hidden-check scoring should account for that uncertainty and future information sets. A fixed 70–85% failure probability has no validation here.
- The proposed population/search sizes are benchmark knobs. We already use 2,048 particles, native rules, risk-aware hybrid search and an invisible-attack bonus. Reducing to 128–512 particles or imposing depth 4–7 without a matched test could hurt.
- Additional visibility is not automatically useful information. Measure whether it changes the next decision; concealment should be valuable for concrete threats, not rewarded as an isolated count.
- Calibration, reconstruction and tactical benchmarks are diagnostic gates. Only controlled play and later arena evidence establish stronger play. No +100/+300 Elo claim follows from this report.

The practical next sequence remains: enforce known facts, measure support and calibration, then test improved offense and observation-aware decisions. The earlier Kimi/DeepSeek assessment is in [Astra's advice review](../astra-submissions/analysis/external-advice-review.md).

## Astra implementation status

The capture-recovery regression reproduced **418/2048 and 433/2048** occupancy support after the lost f1 rook in `bluqrpex`, where occupancy is logically certain. The prototype now passes the four-seed regression. All nine C++ unit suites pass, including new EP and constraint-lifetime cases. The first differential-test invocation missed `FOW_KIT`; that invocation did not execute the referee comparison, and a corrected invocation is running separately. A broader strength measurement is pending.

New code stays under `astra-submissions/implementation/`, with `FOW_CAPTURE_EVIDENCE=0` as the control. I corrected our inherited corpus harness to sample each color by its own move count. Use identical corrected harnesses on both baseline and candidate; old and new aggregate counts are not directly comparable. Full details and limits will be logged after the matched run.

The next audit also counts hypotheses whose **entire rendered observation** matches the real observation, not only agreement on already-visible squares. This may reveal missing negative information (especially pawn blockers and hidden pawn-capture destinations). That is a diagnostic in progress, not yet a claimed defect or a shipped filter change.

Our earlier checkpoint is pushed in `0c2bd4f284e931071273b6c0546872c3d7681d21`. It includes the plans, Duck evidence and provisional archives. New capture-recovery code has not yet been packaged or presented as a strength improvement.
