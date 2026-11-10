# Reference support: fixed development gate fails

All 32 first-attempt private-prefix runs complete, followed by an independent
course-referee, history and policy-row audit. The necessary support gate fails:
**104 of 740 sampled contexts (14.05%) across three games**, versus the frozen
minimum of 20% across four. Do not integrate a range, launch a larger search
or playing batch, or retune this probe from this result.

| Audited measure | Result |
|---|---:|
| First-attempt prefixes / source games | 32 / 8 |
| Sampled native contexts | 740 |
| Locally legal two-step alternatives | 7,425 |
| Alternatives with raw reference probability above 1e-6 | 1,508 |
| Alternatives excluded from the preceding guarded root row | 281 |
| Alternatives outside the preceding legal row | 0 |
| Historical earlier action agrees with searched argmax | 185 contexts |
| Historical action has reference probability at most 1e-6 | 371 contexts |
| Argmax match, positive actual support and at least 1% alternative mass | 104 contexts |
| Games meeting that context condition | 3 |

The successful subset comes from `ck1nptse`, `4mokzo85` and `g485g9uf`.
No first attempt is replaced or excluded. The raw reference distributions,
full private inputs and every local alternative are retained. Some raw
distributions have useful support, but that does not pass the broader frozen
criterion or establish a playing benefit.

## What this actually measures

Each process receives only our views, our moves and recorded own clocks. It
runs exactly one guarded v38 GT-CFR search at the preceding own decision,
with a 0.75-second budget parameter and the unchanged two-worker all-child
scorer. The complete raw last-iterate root row is copied before being freed.
Other prefix decisions are unsearched. It then **forces the historical own
move**, processes the next views and samples up to 32 native ancestry contexts.

The reference distribution is the raw search strategy, not the forced
historical action distribution or a deployed mixed policy. Only 185 sampled
contexts have the historical action equal to that search's argmax. That
limits this reconstructed/off-policy test. The failed gate closes this fixed
configuration; it does not prove that natural on-policy carry cannot work.
The earlier M4 notes040/045 already warn about zero own reach on forced
prefixes; the new counts quantify that boundary for the fresh ancestry API.

For the argmax-matching subset, a pure executed policy assigns **zero** mass
to every different past-own action. Raw search probabilities can support
those actions only as a deliberately chosen reference approximation. The
probe supplies no previous opponent reference rows, full-game reach products,
continuation values or draw-history certification. Native posterior weights
cannot identify those missing factors; the exact rational counterexample
in the [design](../../reference-range-design-20261110.md) shows why.

Native paid thinning is retained, so observer/search timing can alter later
populations. The 7,425 aliases here versus 7,229 in the fixed-shrink ancestry
screen are not a controlled improvement. These are reused development roots;
neither alias counts nor conditional subset rates estimate arena strength.

## Execution and evidence

Source, the reference design and 58 pinned dependencies were pushed and
verified on both mirrors at `3f392f6ce88191124a516551cc717049ab924d69`
before collection. Original run session92058 exits0 after66.688s. All32
processes exit0 without timeout. Original auditor50174 exits0; its independent
checks take3.838s. Both-color real-scorer preflights pass.

The auditor verifies exact actor inputs and forced outputs, complete policy
row normalization, pure-argmax identity, every probability lookup, guard versus
zero-support classification, both private histories, and every emitted
two-step move/view/metadata transition with the course referee. Full native
path repetition counts remain absent, as in291; no stronger legality claim
is introduced. Host checks find no surviving actor/scorer in any of the32
recorded process groups. Cores0–1 are released. Fable's existing watcher is
verified live05:13UTC and is left unchanged.

- [Frozen plan](plan.json), [preflight and rational example](preflight.json),
  [completion](completion.json), [independent audit](audit.json),
  [host cleanup](cleanup.json).
- [Complete compressed policy/context receipts](reference-records.json.gz),
  [corpus manifest](corpus-manifest.json),
  [source](../../experiments/reference-support-20261110/).

Raw outputs and process receipts remain in the authorized Seagate directory
`iamavirus/astra/reference-support-20261110/`. No solver policy change, GPU,
model fit, new version or arena action occurred. No strength claim is made.
