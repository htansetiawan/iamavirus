# Astra 080 — direct v33 candidate versus active v30 screen

## Why this gate

Fable's current tracker calls `iamavirus-v33-candidate-mist-c-v9.zip` a candidate, not uploaded, with a 60-game screen against Misty/v7/v8 but no direct comparison to active arena v30. This fills that missing baseline comparison before considering any Astra artifact. It is only an offline paired screen, not an arena-strength estimate.

## Frozen inputs

- A: Fable v33 Mist-C v9, `fable-submissions/iamavirus-v33-candidate-mist-c-v9.zip`, SHA-256 `9b5915ff5b73fad5b76797f1fe6ceba6b86828e95978e917c0cf610d60568669`.
- B: active arena v30 archive, `fable-submissions/iamavirus-v30-misty-4s.zip`, SHA-256 `20a2e433ca310593f4aa8c38a09fefbd19daf65cd04fcb9f726228e424a8d5c7`.
- Rules runner: `/home/henrytan/git/fow-starter/referee.py`, SHA-256 `2f82ac292bfad29bcb2d701b73c060d1ca8281378b4598f08a620fe5c97255be`.
- Candidate build provenance per Fable tracker: Mist-C v9 archive, source revision `7da1ff1`; compare runner `learning.compare_archives` at repository HEAD `42bbd70` before any further edits.
- Runtime: real referee, `180+2`, 1,000-ply cap; v30's CPython 3.14 native module requires Python 3.14 on PATH; referee itself uses the kit's Python 3.12. Parent comparator uses repo `.venv` Python 3.12 + NumPy.
- Seeds: 44000–44015, in eight color-swapped pairs. Pair seeds are 44000 + 2i. A is v33 in both color orientations.
- CPU: pin the same referee and bot process family to cores 0–1. Lease reserved in `chatroom/cores.json` until 2026-10-11 21:45 UTC. No GPU is used; NVIDIA driver is unavailable.
- Workdir: `/media/henrytan/seagate/iamavirus/astra/v33-v30-screen-20261011/`.

## Precommitted interpretation

Capture every result, reason, plies, final clocks, per-color score, paired score and bootstrap interval from the runner. Stop after the first completed pair containing a crash, protocol error, or time forfeit; preserve all completed game JSON. With eight pairs, this is a screening signal only: do not infer Elo, top-six performance, or promote an Astra build. If v33 is clearly worse or operationally defective, report that; if the score is mixed or promising, require a larger/arena gate before any strength claim.

## Other resource state

At 2026-10-11 20:38 UTC, process inspection found no active training/benchmark/arena job. Fable's core reservation in `chatroom/cores.json` ended at 13:00 UTC and its PID was absent. GPU driver query failed, so training remains deferred. Seagate has 877 GiB free.
