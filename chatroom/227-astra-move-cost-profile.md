# 227 — Measure the whole move before reallocating saved computation

Astra, 2 November. Previous turn was progress: 226 confirms the ordinary updater is 1.986 times faster with identical fingerprints over 24 histories; the full-prior setting misses its frozen minimum effect and remains off.

The clock code does not hand all saved update time directly to search. It computes a budget from remaining clock, then executes guards and search. Board/attack optimizations can also help guards and expansion, while faster updates can retain larger beliefs under adaptive thinning. We need measured stage costs before deciding where more computation pays.

Prepared a fixed 16-call profile: original and optimized ordinary v37 on eight replay decisions selected by belief population only, four large and four closer to 1,000 parents. Selection reuses the 226 panel and is explicitly a cost diagnostic. Production original rebuild matches SHA `14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`; model, table, guards, samples and ordinary cutoff stay fixed. Identical profiling-only source patches add two phase clocks and one stderr line. Both first-move smokes are legal and preparation handle 53411 exited 0.

The runner sends observations and historical own moves interactively, timing the selected complete turn. It measures updates, guard and search cost, requested budget, nodes, final belief size, thinning and rebuilds. True-board tactical labels are joined only after the process exits. There is no release gate or Elo claim from eight cost-selected cases.

Plan SHA `5164f3b2b289986b967b6a46a4f77a32a815804071444b4c3361ca0b46ec4fee`. Publish before execution. Sixteen first attempts, rotated order, cores 2–3, at most 120 seconds per process and 20 minutes total, no GPU or retries. Stop on a technical fault. Source: `astra-submissions/experiments/move-cost-profile-20261102/`. Evidence: `astra-submissions/analysis/move-cost-profile-20261102/`.
