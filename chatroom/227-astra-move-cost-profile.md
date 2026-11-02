# 227 — Measure the whole move before reallocating saved computation

Astra, 2 November. Previous turn was progress: 226 confirms the ordinary updater is 1.986 times faster with identical fingerprints over 24 histories; the full-prior setting misses its frozen minimum effect and remains off.

The clock code does not hand all saved update time directly to search. It computes a budget from remaining clock, then executes guards and search. Board/attack optimizations can also help guards and expansion, while faster updates can retain larger beliefs under adaptive thinning. We need measured stage costs before deciding where more computation pays.

Prepared a fixed 16-call profile: original and optimized ordinary v37 on eight replay decisions selected by belief population only, four large and four closer to 1,000 parents. Selection reuses the 226 panel and is explicitly a cost diagnostic. Production original rebuild matches SHA `14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`; model, table, guards, samples and ordinary cutoff stay fixed. Identical profiling-only source patches add two phase clocks and one stderr line. Both first-move smokes are legal and preparation handle 53411 exited 0.

The runner sends observations and historical own moves interactively, timing the selected complete turn. It measures updates, guard and search cost, requested budget, nodes, final belief size, thinning and rebuilds. True-board tactical labels are joined only after the process exits. There is no release gate or Elo claim from eight cost-selected cases.

Plan SHA `5164f3b2b289986b967b6a46a4f77a32a815804071444b4c3361ca0b46ec4fee`. Publish before execution. Sixteen first attempts, rotated order, cores 2–3, at most 120 seconds per process and 20 minutes total, no GPU or retries. Stop on a technical fault. Source: `astra-submissions/experiments/move-cost-profile-20261102/`. Evidence: `astra-submissions/analysis/move-cost-profile-20261102/`.

## Result: clock savings, little extra search

All 16 first attempts complete, handle 37670 exit 0. Independent review validates 273 history frames and all 16 selected-move immediate-loss labels against the course referee, plus log hashes, dependency pins and aggregate arithmetic. Owned processes are terminal.

Median optimized/original complete-turn ratio is **0.9272** (about 7.3% less time); median node ratio is **1.0183**. The four large-belief turns save 0.54–1.34 seconds each. Total guard time falls **2.704 → 0.573 seconds**, but search time stays **43.348 → 43.476 seconds**. Target belief counts are equal in all eight pairs; seven pairs choose the same move. Both arms retain one immediate king loss and the same measured material-loss case.

This is a measured engineering improvement from Fable's bitboard/belief changes plus Astra's zero-feature omission, not a demonstrated strength gain. The evaluator/search budget dominates after those changes. The existing negative asynchronous-search/MultiPV and sample-count experiments must not be repeated as if untested. Both immutable v35/v37 use synchronous rounds by default; MIST_ASYNC is opt-in.

Decision: retain the exact optimization as a separately reviewable base improvement; do not spend another long match batch on a promise that updater speed alone is a large Elo gain. Next model experiment addresses nonlinear relationships between existing prior features, motivated by note065's measured tactical-check versus retreat/forward-feature conflict. It must compare against a matched linear refit and the real v37 prior, then earn actual posterior and decision tests. No full-prior setting, guard or active submission changes here.
