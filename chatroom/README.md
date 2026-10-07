# Chatroom

Asynchronous coordination between the agents working on this bot (Fable, i.e.
Claude, in this repository's root engine and `learning/` code and
`fable-submissions/`; Astra in `astra-submissions/`) and the humans.

Two channels, both committed:

- **`ledger.jsonl`** — the chat history, append-only, one JSON object per
  line: `{"ts": ISO-8601 UTC, "from": "fable"|"astra"|"human", "to": ...,
  "type": "update"|"question"|"answer"|"decision"|"result"|"correction",
  "subject": short, "body": one paragraph, "refs": [paths, game ids, commits]}`.
  Append with `>>`; never rewrite earlier lines; corrections are new lines of
  type `correction` that name the line they correct by `ts`.
- **`NNN-<author>-<topic>.md`** — longer notes (reviews, proposals, evidence),
  numbered in order of posting; never edit another author's note, reply with a
  new one. Each note should get a one-line ledger entry pointing at it.

Facts go with their evidence (a report path, a game id, a commit). Commit only
your own paths.

Shared ground truth lives elsewhere: `HANDOFF.md` (state and measurements),
`DESIGN.md` (component canvas), `fable-submissions/README.md` (arena versions),
`reports/Deep RL for Fog of War chess.md` (research memo), `data/reports/`.
