# Arena v24 beats Knight Vision v29 in both colors

Astra audit, 2026-10-10 UTC. The games completed October 9 at about 8:40 p.m.
Boston time. Both public replays were fetched after the user reported the wins.

**Both games match the pre-registered v24 replay-book prediction.** Every one of
our 16 moves matches the entry in the published archive. The course referee
reconstructs all 33 moves, 35 frames, both observations and final results exactly.

The authoritative [version map](../../../fable-submissions/README.md) identifies
arena v24 as Fable's Knight Vision replay-book build over v23's engine/model.
The archive SHA-256 is
`36d7932976026875b667c980ef4be3dc0199f736661d0f1b63d17a22c5ffc2b7`.
These games are evidence for that targeted retrieval experiment.

| Game | Our color | Result | Our moves matching the archive | Finish |
| --- | --- | --- | ---: | --- |
| [da7pinqq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=da7pinqq) | White | 1–0 | 11 / 11 | 22 plies |
| [12j9j4qe](https://www.mit.edu/~6.7980/fow/?tab=arena&game=12j9j4qe) | Black | 0–1 | 5 / 5 | 11 plies |

## What won

**White: material ambush followed by an unseen queen attack.** `10.Nxc5` takes
the queen. `10...dxc5` recaptures the knight and clears the d-file. `11.Qxd8`
takes the rook and attacks the king along d8–e8–f8–g8. The queen on d8 is hidden
in Knight Vision's actual reply observation. It plays `11...Nc6`, leaving its
king attacked. The only move preserving the king on the true board was `11...Ne8`.
That is a retrospective label, not information the defender necessarily had.

**Black: a visible bishop threat with an unseen defender.** After `...Qb6`,
`5...Bxf2` attacks the white king. The bishop on f2 is visible, but our queen on
b6 is hidden. `6.Kxf2` removes the bishop and puts the king on the queen's
b6–c5–d4–e3–f2 diagonal. The only surviving reply on the true board was `6.Ke2`.
The queen had remained unseen on b6 since move 4.

Both attacks left exactly one surviving reply. This is more specific than simply
offering material: preparation narrows the defense, and a concealed line makes
the opponent's preferred response fatal. The Black win is a clean example of the
“pressure before bait” skill proposed in Astra note 027.

## What this establishes, and the next use

We have two live arena confirmations, one per color, of recorded losing lines
working against the same opponent version. This supports the user's
lookup/retrieve/apply strategy and Fable's version-specific exploitation.
It does not establish that Knight Vision v29 will repeat forever, or measure a
general strength improvement against other opponents.

Continue tracking this exact matchup and its first divergence from a predicted
observation/action history. Preserve source games and successful lines with
their opponent version. Apply the same repeatability check to duck and the
instructors before choosing which counter-lines to deploy.

One implementation refinement for the next book revision: the archived runtime
looks up `color|current_view` each turn. It does not maintain a strict line-history
cursor or permanently leave the replay book after a miss. Add history/context
guards and distinguish continuation from re-entry in telemetry; identical views
can follow different hidden histories. This does not invalidate these two wins.

## Evidence and reproduction

[summary.json](summary.json) records archive/replay/referee hashes, every book
match, terminal attackers, hidden status and safe alternatives. Raw public
responses are [da7pinqq.json](da7pinqq.json) and [12j9j4qe.json](12j9j4qe.json).
Clock deltas total approximately 0.543 s for our eleven White moves and 0.241 s
for our five Black moves, excluding initialization. Matching moves alone do not
expose the engine's internal `from_replay` trace.

```sh
.venv/bin/python astra-submissions/tools/audit_knight_v24_wins.py \
  --source astra-submissions/analysis/knight-vision-v24-20261010 \
  --archive fable-submissions/iamavirus-v24-hybrid.zip \
  --referee /home/henrytan/git/fow-starter/referee.py \
  --output /tmp/astra-kv24-recheck
```
