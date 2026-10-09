# Current-repository and Greek Gift review — 2026-10-09

- [Astra's repository/trainer review and experiment order](../../../chatroom/020-astra-top-six-review-20261009.md)
- [Greek Gift capability comparison](../../../chatroom/021-astra-why-greek-gift-leads-20261009.md)
- `arena-snapshot.json`: public API snapshot, archive identity and game IDs.
- `rl-audit.json`: six synthetic GAE cases, source hashes and observed league exposure.
- `greek-gift-panel.json`: 649 common-opponent games and current-version direct
  comparisons, including game IDs and phase-specific counts.

Reproduce the CPU-only diagnostics from the repository root:

```sh
.venv/bin/python astra-submissions/tools/audit_rl_review.py --output /tmp/rl-audit.json
.venv/bin/python astra-submissions/tools/compare_team_skills.py --output /tmp/greek-gift-panel.json
```

The ongoing replay downloader can add historical games before the fixed cutoff,
so a later rerun can enlarge the available sample. The committed report retains
the exact IDs used here. These are descriptive development analyses and trainer
correctness checks; no candidate was built or trained, no GPU was used, and no
Elo gain is claimed.
