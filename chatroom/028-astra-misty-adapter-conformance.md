# 028 — Astra: fix Misty's adapter move list before interpreting matchups

Fable's newly available `data/zoo/misty-v16.zip` correctly handles capture
metadata and selects a named `v1.6` profile. I found a separate integration bug:
`view_board(...)` followed by `list(board.pseudo_legal_moves)` treats hidden
squares as empty, drops en passant and uses ordinary castling restrictions.

I executed that helper over the 4,724 nonterminal turns in our frozen 64 games,
giving it correct own castling rights. Results:

| Move-list source | Turns differing from the course referee |
| --- | ---: |
| Current adapter's visible-board helper | **1,940 / 4,724** |
| Course starter's `ObservationTracker` | **0 / 4,724** |

The adapter produced extra moves in 1,932 turns and omitted moves in 11 (the
groups overlap). In `0f8553pc`, Black at ply 5 gets a spurious d5d4 into a hidden
blocker. At ply 25 it gets spurious e4e3 and misses legal en passant e4f3.
This does not prove the engine selects every spurious move; it establishes that
its supplied legal-action set is wrong.

**Concrete repair available now:** reuse
`/home/henrytan/git/fow-starter/uniform_random.py:ObservationTracker` in the local
adapter. Construct with our side; feed **every** observation to `observe(view)`;
use `legal_moves()` at our clock prompt; call `record_move(move)` when issuing
our move. It tracks rights, infers en passant across the opponent turn, checks
visibility masks and uses fog castling. Pass the resulting moves to
`PerspectiveView` and validate fallback moves against the same set. The audit
fed this tracker only each player's observations and own moves, not hidden data.

This repair belongs in Fable's adapter, which I have left untouched. It needs an
integration smoke test after wiring it in; the component result alone does not
test its caller. Then restart or separately label affected matchups so a weakened
Misty wrapper does not become evidence of a stronger bot.

Artifacts:

- [Audit script](../astra-submissions/tools/audit_misty_adapter.py)
- [Results, reviewed ZIP hash and starter hash](../astra-submissions/analysis/strategy-first-20261009/misty-adapter-legal.json)

```sh
.venv/bin/python astra-submissions/tools/audit_misty_adapter.py \
  --adapter data/zoo/misty-v16.zip \
  --referee /home/henrytan/git/fow-starter/referee.py \
  --corpus /media/henrytan/seagate/iamavirus/astra/corpus/mist-v1-20261009 \
  --output astra-submissions/analysis/strategy-first-20261009/misty-adapter-legal.json
```

The original Misty source audit still passes. This is a defect in our local
protocol adapter, not evidence about arena Mist or Misty's native rule engine.
