# Gold: labelled decisions from our own arena games

Built by `python -m learning.curate` from the validated replay cache
(`data/raw`, every frame reproduced by the engine's rules, zero quarantined).
Committed on purpose: this is the data we learn from and argue from.

| file | one row per | contents |
|---|---|---|
| `iamavirus-decisions.jsonl.gz` | decision IAmAVirus made in an arena game | game id, arena version, opponent and its version, our colour, ply, the move and its piece, legal and safe move counts on the true board, whether the move lost the king and whether the capturer was hidden from us, the opponent's best immediate net capture after our move (`exposure`, its move, whether that capturer's square was unseen), the opponent's actual reply, the material swing over the next two plies, plies to the end, the result, and the full view and true board at the decision |
| `iamavirus-games.jsonl` | game | version, opponent, colour, result, reason, length, terminal class, first-decisive-error ply |

Terminal classes for lost games: `king-moved-into-hidden-attack`,
`king-moved-into-visible-attack`, `exposed-king-to-hidden-attack`,
`exposed-king-to-visible-attack`, `already-lost-no-safe-move`,
`lost-on-opponent-move`, `technical:<reason>`.

Labels use the true board only as an offline label; nothing here enters the
bot's features. Regenerate after new games with:

```bash
.venv/bin/python -m learning.ingest --team IAmAVirus --output data/raw
.venv/bin/python -m learning.curate
```

The human-readable summary is `reports/IAmAVirus replay analysis.md`. Any row
can be replayed through any bot mode: `python -m learning.replay_bot <game> --plies <ply> --mode hybrid`.
