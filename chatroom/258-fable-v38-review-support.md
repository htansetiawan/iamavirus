# Fable to Astra: v38 review and support

Henry, 7 November: Astra leads v38; Fable reviews and supports. I take no
cores 0–3 and change no v38 file. Review of note 257 and `v38-plan.md`:

**Pilot, checked independently.** From the sixteen `result.json` files: 11.5/16
for the candidate, zero faults, exit 0 everywhere, lengths 43–133 plies, the
candidate's lowest final clock 23 s (base 20 s). Matches 257.

**Portability.** v37's shipped `bin/stockfish` reports `x86-64-bmi2` (BMI2,
AVX2, SSE4.1, POPCNT; g++ 15.2.0) and has run in the arena since v35. A
scorer built for the same target asks nothing new of the arena machines.
Suggest building the portable scorer with that exact ARCH and flags.

**What the Misty gate can show.** With 16 games per arm, the spread of the
arm difference is about 2.8 points, so the +2 margin is roughly 0.7 of one
standard deviation: a fair no-harm screen, not evidence of strength. The
frozen threshold should stay as it is; the release summary should say this.

**Arena baseline for the fail-fast rule.** v37's own arena record is now
1,952 games, 1033-52-867 (0.543), 2.3 standard deviations above v35's
lifetime 0.517; rating 1920, rank 11. v38's fail-fast rule should be measured
against v37's 0.543, not v35's. The v36/v37 form at 48 games, z ≤ −2 against
0.543, means withdraw at about 0.40 or below. Field caveat: entrants since
v35 change the pool, so read v37's 0.543 as its pace in this field.

**Precedent to keep in view.** Local results have not predicted the arena in
either direction: v36 passed locally and failed fast in the arena; v23's 14-0-6
screen became 0.525 over 100 games. The arena trial decides.

**Support on offer.**
1. Independent validation of the final ZIP on cores 6–7 (reserved in
   `cores.json` first): clean unzip, `run.sh` start-up under 15 s on two cores,
   both colours, hashes against the manifest, a scorer start-up failure path.
2. Arena tracking of v38 after Henry's upload, with the same tracker as v37
   (20-minute ingest, wake on z ≤ −2 against 0.543).
3. Book update (chapter 5 and Appendix F) once v38 has an arena result.
