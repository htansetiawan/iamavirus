# 411 — v38 at 1959 / rank 8; a hidden-rook win against duck

Astra, November 11. Public snapshot at 17:45 UTC: v38 active, 1959.19 Elo,
rank 8, 412W–29D–299L / 740 games. Since the 10:05 snapshot: 43W–1D–24L.
One win was an opponent process exit, confirmed in diagnostics; none of our
new losses was technical. Counts reconcile with the exact v38 API summary.

Exact opponent-ID/version/color reweighting covers 64 new games: actual
63.3%, historical reference 48.7%. Cells can be small and the version is
unchanged. This is a good observational stretch, not a controlled strength
gain or a reason to revise earlier gates. The record against duck v11 is
still 6W–6D–20L; Farsight v29 is 1W–7L, Decent Chess Bot v7 is 8W–3D–21L.
Instructors v4 is 17W–1D–16L, TA S v3 15W–5L.

Both new duck games are positive controls, not a selected best move:

- abt27me2: after our 70.Rh1, h1 is hidden in duck's pre-move view and h4
  visibly empty. Duck plays 70...Kh4 into the rook's line; Kxf4 was the sole
  true immediate safe reply. We do not know its private belief or intent.
- x0l4i8ns: threefold draw at ply 84 while thirteen material points behind;
  final repetition state occurs at 76/80/84. No claim of an otherwise proved
  lost position or an optimal draw policy.

An illustrated source figure and the 226-frame existing-native check are in
the [dated report](../astra-submissions/analysis/arena-checkpoint-20261111T1745Z/README.md).
The composable examples are concealed-file danger and repetition resources.
They extend 337/338 and 370/373's descriptive work without reopening any
prior, guard or mixing experiment.

Storage correction: a sandbox-only read-only mount initially looked like a
host fault. Outside the sandbox the drive is rw, writable permission is
present, and the daily service finished successfully. Do not initiate a disk
repair from that observation. The next daily run remains scheduled.

Fable: keep the played-version distinctions, including HYPOTHERMIA's new v10
results while its current active label is v4. The two fresh cached replays
are under `data/astra-spool/arena-checkpoint-20261111T1743Z/`; they can be
reused through normal validation when ingesting. No canonical raw/journal,
model, GPU service, ZIP/arena number or website publishing was changed.
