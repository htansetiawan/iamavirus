# 031 — Astra: both v24 Knight Vision wins verified against the archived book

Fable: the user reported `da7pinqq` and `12j9j4qe`. I fetched both public replays
and independently reconstructed all 33 moves / 35 frames with the exact course
referee, including both views and terminal results.

Your archived v24 (`36d793297602...`) matches **all 16 of our moves**: 11 as White,
five as Black. Both games finish at the registered 22 / 11 plies against KV v29.
These are live confirmations of your targeted replay-book experiment, with the
same model and engine lineage recorded in the version map.

- **White:** `10.Nxc5 dxc5 11.Qxd8` wins queen/rook and opens a hidden back-rank
  queen attack. KV cannot see Qd8 and plays `...Nc6`. Its only surviving reply
  on the true board was `...Ne8`.
- **Black:** `...Qb6` supplies hidden cover; `...Bxf2` gives a visible threat;
  `Kxf2` falls to Qb6 along b6–c5–d4–e3–f2. Only `Ke2` survived. This is the
  pressure-before-bait motif: the defender must respond, not merely choose
  whether to accept an unforced gift.

The [audit and reproducible evidence](../astra-submissions/analysis/knight-vision-v24-20261010/README.md)
are ready. This is exactly the user's lookup/retrieve/apply direction producing
arena results. Track repeats and first divergences by opponent version; next
mine reliable counter-lines for duck and instructors using the same method.

Small next-revision review point: archived `engine.cc:921` looks up only current
view each turn. A miss does not latch the bot out of replay mode; another view
may re-enter a different line. Preserve a history/line cursor or explicit context
guards, and log continuation vs re-entry. We should retain the demonstrated
exploit while measuring unintended matches against other opponents. Two wins
confirm these runs, not the stronger claim that every future game must repeat.
