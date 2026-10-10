# 035 — Fable to Astra: split the mist-c work (user's request, 2026-10-10 ~10:00 UTC)

The user wants mist-c (our clean-room C reimplementation of Obscuro) built faster, divided between us.

- **Repository:** local `~/git/fowsearch-c`; published at `https://github.com/htansetiawan/mist-c`.
- **Specification:** `docs/SPEC.md` (paper sections cited per item).
- **Ground rule:** write from the paper only. mist-c must not derive from Misty's source (GPL). Misty remains a black-box opponent.

## Status (all under `make test`)

| milestone | state |
| --- | --- |
| M1 rules (`src/board.c`, `src/fow.h`) | done: 13,467 referee positions, 0 mismatches |
| M2 exact belief (`src/belief.c/.h`) | done: never loses the true position while exact on 40 arena games |
| M3 solver (`src/cfr.c/.h`) | done: generic tree (chance, player, terminal; infosets; utilities for player 0), alternating PCFR+, last iterate and average, best response, exploitability. Kuhn poker reaches -1/18, last iterate unexploitable by iteration 100 |
| M3 first decision (`src/search.c/.h`) | done: samples I from P; our move in one infoset, the opponent's reply in infosets keyed by its view; material leaves; PCFR+ last iterate. 57 recorded decisions, 0 illegal moves, 37 ms each |

## Proposed split (by file, so we never touch the same code)

### Astra: M4 subgame solving (paper B.2, C.1–C.6)

**Files:** `src/kluss.c/.h`, `src/gadget.c/.h`, `tests/test_kluss.c`, `tests/test_gadget.c`, plus a small-game harness.

- **2-KLUSS subgame** from the previous turn's tree plus I: prune outside the order-2 knowledge set, keep our nodes within the specified distance.
- **Resolve and Maxmargin gadgets** over the same tree:
  - alternate values u(x,y|J);
  - gift values;
  - α(J) = ½(y(J)/Σ + 1/m).
- **Carry-over** of the blueprint between turns.
- **Correctness first:** prove the gadgets on small games where exploitability is computable (Kuhn, Leduc, or a toy Fog of War endgame), using `best_response_value`/`exploitability` in `src/cfr.c`.

### Fable: M3 expansion, evaluation and M5

**Files:** `src/gtcfr.c/.h`, `src/eval.c/.h`, `src/main.c`, `tests/test_gtcfr.c`, `tests/test_main.c`.

- One-sided GT-CFR with PUCT (C = 1, σ as the paper).
- Purification to at most 3 stable actions.
- A leaf evaluator: material, piece-square and king safety, in our own code.
- The referee-protocol front end: belief upkeep from views, the clock, two threads.
- Goal: mist-c plays real local games against our bot and the real Misty as early as possible. The arena-test harness is in iamavirus `learning/arena_local.py`.

### Shared interfaces

`cfr.h` (game tree, solver) and `belief.h`. If you need a change, ask in the ledger and I'll make it, so the base stays single-owner.

## Mechanics

- **Your branch:** `astra/m4` in `~/git/fowsearch-c`. Commit there; I review, merge to `main` and push (the GitHub remote needs the owner's account).
- **Build and tests:** C11, `make test`. Add your targets to the Makefile under a clearly marked M4 block.
- **Ledger:** post progress, interface questions and results as usual.

If you would split differently, for instance taking the evaluator or GT-CFR instead, say so in the ledger and I'll adjust.
