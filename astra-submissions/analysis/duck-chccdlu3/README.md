# Arena v10's win against Duck v4

Public game [chccdlu3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=chccdlu3), completed 2026-10-07 2:33:37 PM EDT. IAmAVirus played White, arena version 10; Duck played Black, version 4. Result 1–0 after 48 plies, reason `King capturable`.

Arena v10 is the Fable artifact uploaded under the v12 label, now mapped to `fable-submissions/iamavirus-v10-hybrid.zip`. Use the [shared mapping table](../../../fable-submissions/README.md) and hash `6f57a44ec81424cb6ca7a21522191924007f2bd647c0424dd553a0ceece47567`; this is not the independent Astra v10 ZIP.

White's **24.Re8** placed a rook on e8, hidden in Duck's observation, attacking Kg8 along the eighth rank. Duck played **24...f6**, leaving its king attacked. **Kxg7 was the only legal move that survived immediate adjudication**. The final move was a pawn move; Duck did not walk its king onto e8 or move the king at all.

This is a concrete example of the offensive opportunity already represented by the engine's hidden-king-attack bonus. The replay cannot establish whether that bonus caused the move, nor whether the version is stronger overall. Keep the win alongside the losses when curating data.

[summary.json](summary.json) records the public replay checksum, all final legal moves, the sole surviving alternative and attacker visibility. Every frame and all legal-move survival labels were checked against the course referee: **49 frames, 1,641 move checks**.

```bash
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/analyze_terminal.py \
  astra-submissions/snapshots/arena-monitor/20261007T183951Z/chccdlu3-replay.json \
  --output astra-submissions/analysis/duck-chccdlu3/summary.json \
  --referee /home/henrytan/git/fow-starter/referee.py
```

## Monitoring

The public GET monitor started at 2026-10-07 2:43:54 PM EDT for 24 hours, with a five-minute interval and sequential requests paced at one per second. It caches new completed IAmAVirus games and appends Duck results or protocol anomalies to the shared ledger. Run metadata and snapshots live under `/media/henrytan/seagate/iamavirus/astra/arena-monitor/`; `latest.json` is the current status and `run.json` records PID and script hash. The monitor does not upload bots or use the GPU.

At the 2:48 PM EDT snapshot, our arena v10 had 17W–13L. Duck had 1904.79 Elo and an **active-v4** record of 819W–54D–719L. Its lifetime team counts are different; neither version's raw record controls for opponent mix.
