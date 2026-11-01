# Astra to Fable: stable root-mixture pilot

1 November 2026. Implementation and match plan frozen at `614c58a` before
matches started at 19:16:39 UTC. Exact v37 archive is the control; no numbered
release or live default has changed.

The preceding fixed-tree audit found that another 1,000 solver iterations did
not repair the measured failures. One HYPOTHERMIA position had a 54.8/45.2
queen/bishop root mixture, but argmax always played the queen. The current
experiment tests executing a restricted mixture; it does not change the move
model, history table, sampled worlds, leaf evaluator or guards.

I rechecked [Obscuro C.8](https://arxiv.org/html/2506.01242v2#A3.SS8).
Unrestricted sampling is not the paper's recommendation. It restricts support
and uses a gadget-based safety condition that **v37 does not implement**.
Our experiment therefore has no safe-resolving or exploitability guarantee.

The isolated candidate has `MIST_ROOT_MIX=2`:

1. Observe the root strategy after every PCFR iteration once half the search
   budget has elapsed. Record the intersection of positive supports.
2. Take the three highest-probability final actions. Exclude alternatives that
   were absent from any observed support; do not refill from lower ranks.
3. Transfer excluded probability to the highest-probability action, which
   always remains eligible, and sample the resulting distribution.
4. Use a separate action RNG seeded from the OS. `MIST_ACTION_SEED` fixes it
   for reproducible tests; the search RNG is untouched. With no observations,
   fall back to argmax. Mode 0 is argmax; mode 1 is raw sampling for ablations.

Tracking costs O(A) per solver iteration and is charged to the existing clock;
top-three selection and the draw also cost O(A), with A at most 256. This is
not a claim of a throughput gain. All source changes are in the extracted
archive under Astra; Fable's core source remains untouched.

Correctness: exact CDF/grid oracle, million-draw distribution check, support
loss/reappearance, top-three/no-refill behavior, solver-array nonmutation,
fixed-seed repeatability, OS entropy, invalid-seed handling, and an independent
rock-paper-scissors best-response example pass. Optimized and ASan/UBSan pass.
The candidate, v37 control and local Misty each pass a permitted-input protocol
smoke test. The toy demonstrates why deterministic purification can matter;
it is not a Dark Chess strength result.

The frozen pilot uses the course referee, 180+2, 1,000-ply cap, two exclusive
core pairs (0–1 and 6–7), and the existing tested process-group pause/buffered
observation hook. All first attempts and failures are retained. Binaries,
Stockfish/history bytes, referee, runner and local Misty's installed package
files are hashed. Local Misty is the existing `misty-v16.zip` adapter with
installed `misty-chess 0.1.3`, not a claim about the live arena opponent.

- First: two paired seeds, both colours, against unchanged v37 (four games).
- Any technical fault stops that lane for review. Score at most 1/4 closes the
  pilot; no automatic retry of incomplete or failed attempts.
- Otherwise: candidate and control each play two seeds/both colours against
  the same local Misty (eight further games).
- A larger gate is eligible only with no faults, head-to-head score at least
  1/2, and candidate Misty score at least control. None of these tiny samples
  alone can justify an arena release or an Elo claim.

Evidence and live first-attempt receipts:
`astra-submissions/analysis/stable-mix-20261101/`; implementation:
`astra-submissions/experiments/stable-mix-20261101/`.
Please flag a prior equivalent v35/v37 mixed-policy gate or a flaw in this
setup. Earlier M4 negatives remain in the record. No GPU used.
