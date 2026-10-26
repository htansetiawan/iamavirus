# Evidence behind the Claude-summary review

Astra, 25 October 2026 Pacific. The user supplied the full document after the
artifact URL yielded only its viewer shell. This review addresses that pasted
text. The checks below are source inspection, primary-source research and one
public GET snapshot; no new playing-strength experiment or training run.

Human brief: [Review 3](../../../docs/review-claude-summary.md).

## Source and release audit

The deployed archive is `fable-submissions/iamavirus-v35-mist-c-v14.zip`, SHA256
`24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`.
Its `main.c`, `belief.c`, `gtcfr.c`, and `eval.c` match mist-c commit `97b60f1`.
The current separate checkout is `2dc62ee`, including later experimental code.

`source-audit.json` records the checks. Reproduce without training or network:

```sh
python3 astra-submissions/analysis/competitive-review-20261025/audit_summary.py \
  --output /tmp/iamavirus-summary-audit.json
```

The audit uses the existing local mist-c checkout and replay snapshots; it is
not a standalone distribution. Its snapshot input is pinned, while rechecking
the reporting source and local snapshot list can reflect later repository changes.

1. **Checkout and release differ.** Hazard knobs and `MIST_GUARD_UNIFORM` in the
   pasted appendix are absent from all v35 `src/` files. `MIST_MATERIAL_GUARD`
   is present. In current checkout `gtcfr.c`, setting fitted hazard off can leave
   standing fog hazard at 0.5. Thus “all later work off by default” must not be
   used to claim current checkout behaviour equals v35. No behaviour-equivalence
   test was performed here.
2. **Board deduplication loses history.** Release `belief.c:56–60` deliberately
   keys by board, excluding opponent history, retaining the first history as
   representative. The same comment documents the memory rationale. The
   summary's “infosets keyed by own history” is true of the subsequent search
   but does not restore histories discarded upstream. This is a real
   approximation, not evidence yet of its frequency or Elo cost.
3. **The 24/40 number is mislabeled.** mist-c README's cap table and the
   release comment count games exceeding the cap. The separate truth-loss
   measurement counts plies. Report these distinct quantities, including cap
   and revision, rather than relabeling overflow as truth loss.
4. **The two guard weightings are approximate after merging.** The source
   notes “up to merges.” If histories have weights `w1,w2`, storing their
   sharpened sum and untempering gives `(w1^t+w2^t)^(1/t)`, generally different
   from `w1+w2`. Calling that recovered weighting the exact fitted posterior
   overstates the implementation. Raising the board cap does not correct this.

## A reporting defect affecting priorities

In `learning/daily_insights.py:74`, snapshot keys come from the first 16
characters of directory names such as `2026-10-25T101243.632817Z0000`.
At line 130 the game lookup key is instead `20261021T1200`.
Lexicographic ordering places the latter after every hyphenated 2026 key.
For a team present in those snapshots, `rating_at` therefore chooses its latest
cached rating even when the game is days older.

The audit reproduces this for October 18, 21 and 24. Each selects October 25;
parsing UTC instants selects an appropriately earlier snapshot. Consequently
the reported seven-day total **+881** and per-opponent figures are not historical
rating flows. Previous Astra notes repeating such figures also need this
correction. Result counts remain separate and are not invalidated by this bug.

**Requested Fable repair:** parse both inputs as UTC datetimes, use only prior
snapshots, report missing/stale coverage, and label the result an approximation
unless using actual pre-game ratings. Add before/after/between-snapshot tests.
Recompute old comparisons before ranking work by points lost. Do not infer
“pool deflation caused the decline” from one rating series.

`TOP6` is also fixed to Greek Gift, Knight Vision, Strongly Invisible, Decent,
duck and Instructors. At the new snapshot Crimson Fog and Mist Opportunities
are fifth and sixth. Preserve an explicitly named historical cohort and add a
dated current-leaders cohort; changing the membership silently would also
invalidate comparisons. The king-move table compares us across all opponents
with leaders only in our games, which is not a matched strategic comparison.
Future tables should match seats, opponent versions, phase and material state.

The daily script still defaults to `/media/henrytan/seagate/iamavirus-data`;
training symlinks still target that mount. This review leaves repair to the
shared pipeline owner. Do not mistake successful ingestion/reporting for a
fresh training export or an updated deployed model.

## Frozen competitive evidence

One-shot public read captured `arena/snapshots/20261026T040940Z/`:
leaderboard, latest 100 own results and team versions. Snapshot time is
**26 October 00:09 Boston (25 October 21:09 Pacific)**. IAmAVirus v35:
1908.95, rank 10; Greek Gift v25: 2379.30, rank 1.

The latest 100 contain duck v6 1W–1D–8L, Instructors v4 6W–0D–8L,
Mist v2 4W–0D–4L, Crimson v3 2W–0D–6L. These small windows are volatile:
the earlier same-day latest-100 duck record was 6W–4L. Neither proves a
change in engine strength. Prefer the seven-day version-conditioned results
for selecting targets, with future confirmation on a fixed evaluation cohort.
The public API is read-only here; no replay downloader or monitor daemon was
started. Monitor lock/state files are operational and excluded from publication.

## Limits of the “ideal system” argument

- An exhaustive board set is not an exact distribution over information
  histories. Unknown opponent behaviour also prevents claiming exact weights.
- A per-legal-move floor prevents numerical zero but a length-T sequence can
  still have exponentially tiny mass. A low probability for the one true board
  is not sufficient to diagnose tactical risk: measure the summed mass of all
  worlds with the same dangerous consequence.
- If a **whole threat family** has mass `p=.0006`, an independent 32-draw
  sample sees it with probability `1-(1-p)^32`, about 1.9%; 128 draws give
  about 7.4%. This illustrates why brute-force sample growth can be inefficient;
  it is not a measured sampling probability for a particular loss. Weighted
  sampling without replacement has different inclusion probabilities.
- A targeted sampler can reserve coverage for distinct tactical consequences
  while preserving their probability weights. Oversampling danger as if it
  were posterior mass instead creates an excessively pessimistic objective.
  Full correctness requires accounting for the actual sampling scheme.
- More Stockfish depth still gives a full-information continuation. Two
  histories with identical boards can have different fog values because the
  opponent knows different things. A full-board scalar cannot represent both.
- Removing all guards is not a theorem implied by fitting a better value.
  Conversely, tightening guards is not a proven upgrade: our fixed 40-game
  guard candidate finished 16W–24L with no promotion evidence.
- “Safe re-solving” requires the appropriate information sets and valid
  continuation bounds. History truncation, approximate leaves and a changed
  root distribution require their own analysis. Obscuro's selected mixing and
  purification are more nuanced than either always sampling or always argmax.
- Failed additive hazard terms do not prove all fog-specific values fail.
  Likewise, the four-times teacher diagnostic is not evidence that search
  never benefits from more time; it holds beliefs and masks fixed and measures
  immediate safety on a deliberately selected panel.

## A bounded algorithmic direction, not another blanket rewrite

Prioritise a **history-conditioned tactical challenger**, using opponents as
sources of reusable motifs rather than player-name rules. Candidate motifs:
unseen slider arrival, bait followed by line opening, forced king evacuation,
and advantage conversion. These are proposed labels, not verified claims about
the private algorithms of particular arena leaders.

For diagnosis, distinguish: missing true threat from the retained belief;
present but underweighted threat; threat omitted by search sampling; useful
action removed by guard; reply not expanded; inaccurate leaf; and a modelled
loss deliberately accepted for another benefit. Several may coexist. Include
wins, draws and ordinary positions, not only recorded terminal errors.

A small representative pilot should establish which of these can be repaired
at the same clock cost. A bounded history-mixture per board is worth testing
against the current single representative; keeping every history immediately
would repeat the known memory failure. An offensive model must condition on
opponent information, not merely count attacked squares or call hidden threats
automatic wins.

Learning should compare **alternative actions from the same information
history**, retaining legal excluded actions with provenance. Full boards and
counterfactual rollouts may label the critic; the actor receives only available
history. Terminal outcome and tactical targets need separate reporting.
Search teachers must earn trust through outcomes, not just bigger budgets.

For resource allocation, use ranges for:
`frequency of recoverable cases × expected score recovered × confidence /
total development, training and validation cost`.
Do not assign fabricated +100 Elo estimates. Maintain a separate leader-facing
challenge set so an easy mid-table gain does not permanently displace the
long-term objective. Small pilots reject bad directions; promotion needs
complete-game evidence with uncertainty.

The Oct11 M4 scheduler was already implemented, correctness-tested and rejected
on its diagnostic screen; the broader M4 tests also failed to establish a
promotion. “Finish M4” is not a fresh unexplored idea. Its next useful step
would identify a specific reply-tree defect and demonstrate its repair.
[M4 closure](../m4-closure-20261011/README.md),
[broader gate](../m4-gate-20261011/README.md).

For throughput, the existing persistent-teacher pilot reduced six queries from
18.56 to 6.87 seconds. Reuse that work, but do not project its 2.70× gain onto
the entire pipeline. Compression should preserve action distinctions and
rare tactical events; low board-reconstruction error alone is not useful proof.

## Additional primary research worth retaining

The human brief links Obscuro, Libratus, StrangeFish2, PSRO and Student of Games.
These are lessons and proposed transfers, not a claim that one combined
algorithm inherits all their guarantees.

A newly found [January 2026 endgame preprint by Gehnen and Stannat](https://arxiv.org/html/2601.18813v1)
analyzes king+queen, king+rook and king+two-rooks versus a lone king. It identifies
a difference from ordinary chess: one rook does not guarantee a win in every
starting configuration. Its constructive results assume knowledge of the
initial king position and ignore draw rules. A small information-state endgame
controller could be a useful conversion specialist **if our data shows enough
such missed wins**, after adapting repetition, move limits and clock rules.
This is an option to measure, not a higher-priority project by default.

[ESCHER](https://www.mit.edu/~gfarina/2023/escher_iclr23/) remains a credible
learned-regret challenger; its neural Dark Chess benchmark did not establish
superiority over Obscuro. Preserve the distinction between ESCHER's sampling
requirements, ordinary search distillation and PPO. They are not interchangeable
names for the same training loop.

## Review boundary

No source in Fable's engine/trainer was edited; no training, GPU lease,
tournament, ZIP or arena mutation occurred. This report requests corrections
and a bounded next plan, with the existing 24-hour committee review. It does
not silently resume the paused/blocked development campaign.
