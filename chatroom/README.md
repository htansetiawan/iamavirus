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

## Messages from the human: `msg_NNNN.md`

The human may not have a terminal, only a phone. Their channel is a file:

- **Write** `chatroom/msg_NNNN.md` (four digits, next free number: see
  `INBOX.md`; any `msg_*.md` name is accepted). Free text. Optional header
  lines at the top: `to: fable` / `to: astra` / `to: all` (default all),
  `priority: urgent` (the agent interrupts its current work). Commit it to
  `main` from the GitHub web or mobile editor ("Add file" inside `chatroom/`).
- **Agents poll** `origin/main` for new `chatroom/msg_*.md` at least every
  10 minutes while active (Fable runs a 2-minute fetch watcher) and, on every
  new message: (1) append a ledger line of type `ack` naming the file, within
  minutes; (2) act on it; (3) reply in `chatroom/msg_NNNN-fable.md` or
  `chatroom/msg_NNNN-astra.md` — short, plain Markdown, readable on a phone,
  with the evidence paths; (4) update the row in `INBOX.md`. Never edit the
  human's own file; a follow-up from the human is a new `msg_` file.
- **`INBOX.md`** is the one page to open on the phone: every message, newest
  first, with each agent's status (`—`, `ack`, `answered` + link).
- **Pull before push, always**: push with `tools/push_safe.sh` (fetch, then
  push if nothing new, else rebase onto `origin/main` with autostash), so the
  human's commits are never rejected or overwritten; never force-push `main`.
