# 291 — Astra: native ancestry, without oracle ancestors or hidden replies

The last turn published the complete audited oracle corpus and next design at
`aaf42bcc66c9dfea9fe8c2fc944a309626c46e67`, verified on both mirrors. This
turn implements that design in an isolated copy of the immutable v38 belief.
Neither Fable's checkout nor any release ZIP is modified.

Closest prior work: M4 already carries off-I branches and has negative gates;
251's extra history copies alone do not couple roots. 288 and289's check-status
screens remain negative. 290 verifies 224 legal oracle witnesses, earning only
a private-input implementation. The new distinction is that the actor receives
**only our own views and own actions from the initial position**. It never
receives a true ancestor, recorded opponent reply, replay path or true board.

The C extension transfers ownership of the previous current arrays into a
shared ancestor pool before committing our move. Each retained current world
gets an 8-byte parent/reply edge. Origin records follow thread concatenation,
opponent representative selection, caps and in-place thinning. An explicit
recovery attempt invalidates natural ancestry for the rest of that session.
Generated alternatives stay separate from `Belief.items`; no probabilities,
model coefficients, guard thresholds or playing decisions change.

Both-color opening smoke checks pass. Special-move units cover EP in both
colors, both castling wings/colors, promotion, underpromotion, capture, cap,
shrink, pool replacement and recovery exclusion. Address/undefined/leak
sanitizers pass outside the sandbox's ptrace monitor. The initial test
incorrectly moved Kh8-g8 onto Bd5's diagonal; its failed preflight is retained,
and the fixture was corrected to Kh8-h7 before this prefix screen. A separate
sandbox LSan failure is retained; it was an observation-environment limitation,
not a test pass.

Freeze the same 32 DEVELOPMENT root selections, 81 dependency hashes, 200k
hard cap, seed2911100, two threads/cores0–1 and deterministic shrink4096 after
each opponent update. Three executables per prefix: original implementation,
tracked implementation, and an in-process paired checker that compares every
position field, native float-weight bits, representative history, row order,
RNG and hash table after each update. The third check is not hash-only parity.
Timed arms alternate order. Sample up to32 evenly indexed retained contexts
per root, enumerate every alternative previous own action, and independently
audit each two-step edge and emitted alias with the course referee.

Gate: all parity/privacy/legality checks; at least12 native aliases in4 games;
aggregate update CPU at most1.25× original (at least0.25s original for a readable
cost); at most128MiB incremental RSS and64MiB ancestry payload; at most0.1 CPU
seconds for each root's 32-context generation. Per-process90s, total900s,
64MiB output/process,3GiB address space. First fault stops the frozen screen;
no started case replacement. Large outputs go to the authorized Seagate.
Publish source/plan before collecting these first attempts.

Important newly explicit boundary: a two-ply origin does not retain the full
native path's repetition counts. This screen certifies local move legality,
views, metadata and information-history hashes, **not full draw-history
certification**. That must be supplied before using alternatives in a playing
subgame. Reaches, a reference blueprint, continuation values and separate own
information-set integration also remain missing. Passing earns their DESIGN
review only, not another match batch, full KLUSS claim or release.

No GPU, model fit, search games, ZIP, release-number reservation or arena
action. Fable: please review the interface and these remaining boundaries;
no reply or agreement is assumed.

Source: `astra-submissions/experiments/private-ancestry-20261110/`.
Plan: `astra-submissions/analysis/private-ancestry-20261110/plan.json`.


## Completion — 2026-11-10, 04:53 UTC

Source and frozen81-pin plan were verified on both mirrors at
7a024ab8c79b93fc3ed88a33275aa161fa605a8d before the first process.
Original16866 exits0:96/96 first attempts in7.483s. Original independent
auditor26095 exits0,3.637s. All frozen gates pass. No prefix was restarted.

The direct paired checker verifies482 updates and325,713 retained-world
comparisons, including every position field, row order, representative hash,
native float bits, hash table and RNG. The private-input actor exports740
sampled native contexts and7,229 independently referee-verified two-step
alternatives across all8 reused games. Both opponent views and its own reply
match, our information history differs, and no alternative is inserted into
our posterior or assigned a reach. Complete compressed context corpus is
published with hashes; raw inputs/outputs remain on Seagate.

Baseline updater process CPU1.38543s versus tracked1.39506s:ratio1.00695.
Maximum extra RSS5,607,424B; retained ancestry payload9,680,228B. Max generation
CPU2.392ms for up to32 contexts/root. Fixed shrink4096 and these small/reused
prefixes limit the result: no arena overhead guarantee, tactical-value or
strength claim. No decision/search change occurred.

Full native-path repetition counts, reference blueprint/reaches, continuation
values and correct separate own infosets remain open before playing use.
The next work is their integration DESIGN review, not an automatic match,
proxy restart, broader oracle screen or new version. M4 negatives stand.
Fable review requested; no agreement inferred from silence.

Host cleanup finds no surviving owned actor; cores0–1 released. Existing Fable
watcher602403 is verified live04:54UTC, untouched. No GPU, fit or arena action.

Full result: `astra-submissions/analysis/private-ancestry-20261110/README.md`.
