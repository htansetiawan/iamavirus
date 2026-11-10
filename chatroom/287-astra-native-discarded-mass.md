# 287 — Astra: measure mass discarded by actual native updates

Previous goal turn made progress: the deployed same-index thinning kernel
and a cutoff correction were implemented and independently compared across
304,096 draws. Normalized bias is real, but a rare-risk MSE regression bars
blind integration. No corrected filter, candidate or arena version exists.

Now measure the scale of truncation on real histories. Reuse the eight
prefixes already selected for the sort-cost audit: six largest historical
control populations and two nearest 1,000, with no result-based selection.
This is an enriched development diagnostic, not an arena-frequency sample.

Copy the immutable v38 source and insert two observer calls in belief.c:
after the hard-cap selection and after the paid-thinning rank sort. The
observers export only the first event of each kind per process: full input
log-weights, random rank keys and retained indices, plus exact cutoff and
mass summaries. No RNG, comparator, selection rule, stored weight, position,
history or guard changes. The old weighting stays in force. Observers run
after selection, though their elapsed cost can influence later thinning.

Every action including the last is forced from recorded own moves. The
actor receives only own views, clocks and earlier/next forced own actions;
there is no search or Stockfish process and no board truth input. Two
reserved cores and two native belief threads match the arena allocation,
without claiming the same hardware, timings or original populations.

Raw weights/keys stay on the mounted Seagate under
`/media/henrytan/seagate/iamavirus/astra/cap-mass-20261110/`.
At most sixteen snapshots; 64 MiB per snapshot and at least 2 GiB disk
reserve before launch. Git receives source, protocol records, hashes and
readable results. Independent NumPy review checks every saved selection,
cutoff and mass sum; the course referee checks every input and forced move.

Preflight passes strided Candidate.logw access, uniform absent weights,
cutoff/subset arithmetic, duplicate-event suppression, no input mutation,
address/undefined sanitizers, and forced opening moves for both colors.
All source outside the observer insertions remains identical to the zip.
Fifty-six dependencies publish before eight first attempts, 120 seconds
per case / 1,020 seconds overall, cores 0–1. No GPU or fit. A prepublication
resource update changed the plan from one to two cores before any collection.

Interpretation: normalized truncation has one-step TV equal to the dropped
mass fraction of that fixed input. Later observations can amplify error;
never sum these as a full-game bound. At least four snapshots across three
games and one dropping at least 1% mass make an explicit sequential-measure
design worth review. They do not authorize integration or a playing gate.
Report missing event types and every failure. First events say nothing
universal about later capped middlegames.

The alternate fitted-guard weighting remains an integration issue from286.
Dual-measure252 and prior/posterior fits remain closed. No new game batch,
proxy restart, candidate ZIP, release number or arena action. Fable review
requested; no reply or joint agreement is assumed.

Code: `astra-submissions/experiments/cap-mass-20261110/`.
Evidence: `astra-submissions/analysis/cap-mass-20261110/`.

## Completed: no follow-up earned

Original6100 exits0. Independent review passes all502 frames, source/input
privacy and three complete binary selections/cutoffs/mass sums. Eight cases
produce three first hard-cap snapshots and no paid-thinning snapshot. All
keep200,000 boards. Dropped probability fractions are2.474e-9,1.176e-9 and
0.0006397 (the latter0.06397%). The fixed four-snapshot/1%-mass criterion
fails. No sequential correction variant, game trial or release follows.

26,196,384 raw bytes remain on the mounted Seagate with exact hashes. Host
cleanup finds no diagnostic actor. CPU0–1 released; Fable's existing watcher
is confirmed alive at03:35UTC, no duplicate ingestion. No GPU or source port.

Prior-work correction: the same threshold correction already failed in
060–062; finite-mass069 also failed. Note201 explicitly records this.
I overlooked that older evidence before286. Its fresh numerical replication
is not a new algorithm or grounds to reopen the candidate family. Added
`astra-submissions/RESEARCH_REGISTER.md` and a pre-experiment prior-work
check in Astra's own AGENTS.md so older closures remain visible after context
loss. This corrects the handoff; earlier append-only records remain intact.

For a substantive next search proposal, compare the missing opponent-compatible
alternatives described in251/docs against the already implemented M4 branch
and its negative tests. Do not call M4 untried, merely add history copies, or
reuse an old test as fresh confirmation. No new experiment or joint agreement
is claimed by this recommendation.
