# Analyses of 2026-10-10 (notes 030 and 031)

Standalone scripts, run from the repository root with the venv Python. They read
the replay mirror (`data/raw`); the local-game scripts read `data/arena_local/builds`.

| script | question |
| --- | --- |
| `duck_losses.py [team]` | every loss to a team: collapse ply, how the king fell, killer, our shelter |
| `duck_all.py [team]` | a team's record against everyone, and how its own king falls |
| `duck_fingerprint.py` | move-taxonomy rates: us vs duck, the top five vs duck |
| `king_bait.py`, `king_fog_era.py` | our king moves and captures into open fog lines: next-ply death rates by era |
| `check_rate.py` | how often each team plays an available hidden check |
| `determinism_v.py [teams]` | per-move determinism of each team's current version (Knight Vision v29: 1,336/1,336) |
| `bait_rate.py`, `bait_made.py`, `bait_kind.py`, `bait_table.py` | hidden-cover baits next to the king: who takes them, by check and piece; the rate tables in `engine.cc` (v25, v26) |
| `bait_avail.py` | covered check-baits available to us and how often we played them |
| `bait_games.py [team]` | the games where a team's king took the bait |
| `misty_local.py` | local games against the real Misty: engine score vs true material |
| `classifier/build.py`, `train.py`, `export.py` | the v26 opponent classifier: dataset, held-out evaluation, weights header and parity vectors |
| `classifier/check_local.py`, `check_arena.py` | its verdicts on local sparring games and on our arena games |
