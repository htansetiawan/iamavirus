# 058 — Astra: dominance stays off; fresh hidden-check diagnosis

Finished the frozen seed14, both-color, 180+2 screen against C v8:
**control 2W–0L; dominance 0W–2L**. All 119 M4 decisions are clean; all 242
frames validate; process cleanup is clear. Every treatment turn completed its
profile, but only one actual move changed in 82 treatment decisions (Black
ply81, already down 800cp). Both openings diverged before any redirect; this
does not establish a causal strength loss. It offers no reason to promote the
option or run a bigger gate. No engine default changed, no ZIP, GPU untouched.

One control win is a useful offensive motif: as Black,
`d4 e6 e4 c5 d5 exd5 f3 Qe7 exd5`, then White's king is capturable. The queen
on e7 is hidden before White captures; that capture opens the king's file.
Retain this as *capture lure opens a hidden line*, not a player-name rule or
a proven opening book.

The two new equal-material v30 failures were fed to our C engine through their
complete public observation protocols, with truth used only for checking:

- **c4ak2ldi:** C finds the only defense Re2-e8 in cold, searched-prefix and
  optional-witness probes.
- **gjlnku86:** the cold search plays losing Ne5xd3 in both seeds21/22. Warm
  seed21 finds Nc6, but warm seed22 still loses. A witness in seed21 adds a
  fatal representative without changing the losing choice. These are one-second
  development probes, not strength evidence; warm also changes Stockfish state.

Crucial calibration distinction: the exact true board has **0.125%** posterior
mass, but the **Qa4 hidden-check family has 0.773% across 12 of 1,135 worlds**.
All 1,135 observations validate. Ne5xd3 loses in those worlds; Nc6 and c6 have
zero immediate-loss mass in the full belief. Cold seed21 misses every fatal
root, but seed22 contains the truth, assigns 8.05% normalized gadget reach to
fatal roots, and still captures. Coverage alone is not the whole problem.

Additional wrapper clue: among 1,755 new public v30 decisions, only **five**
take less than 50ms by replay clocks, and **two are fatal** (`c4ak2ldi`,
`gen2p4rz`). The latter has three consecutive 1.9–2.7ms moves before losing.
These are rare fast-return cases with ample clock, separate from the time
forfeit in 056. No internal cause is inferred and no Misty source was inspected.

Evidence: `astra-submissions/analysis/m4-dominance-screen-20261011/README.md`
and `astra-submissions/analysis/m4-live-corpus-20261011/timing.json`.
Both study directories retain hashes and raw/compact evidence. All jobs from
this screen and its probes are terminal; no background training remains.
