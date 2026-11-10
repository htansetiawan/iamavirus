# Native private-input ancestry passes its development gate

The isolated C implementation generates alternatives from naturally retained
belief hypotheses, starting at the standard board and receiving **only our
views and our moves**. The earlier oracle's true ancestor and recorded hidden
reply are absent from actor inputs. It passes the frozen parity, local
legality, coverage and cost gate. This is a representation prerequisite,
not a playing-strength improvement or a new arena candidate.

| Frozen development measurement | Result |
|---|---:|
| Prefixes / games | 32 / 8 |
| First-attempt executions | 96 / 96, all exit 0 |
| Direct per-update parity comparisons | 482 |
| Direct retained-world comparisons across updates | 325,713 |
| Sampled native contexts | 740 |
| Referee-verified two-step alternatives | 7,229 |
| Baseline / tracked updater process CPU | 1.3854 / 1.3951 seconds |
| Observed updater CPU ratio | 1.00695 |
| Maximum incremental process RSS | 5,607,424 bytes |
| Maximum retained ancestry payload | 9,680,228 bytes |
| Maximum generation CPU, up to 32 contexts/root | 2.392 ms |

The paired checker runs the original function bodies and the extension in
one process. It compares every retained position field, original float-weight
bits, representative history, row order, RNG and hash table after each
update or shrink. Separate processes supply cost measurements, with arm
order alternated. Their state digests also match. The generator is checked
not to mutate the posterior or its RNG.

An independent Python/course-referee audit reconstructs every exported
ancestor's two moves, verifies their legality, current board metadata, our
observations against the actual private input, both opponent observations,
and information-history increments. Every emitted alternative changes our
earlier move, preserves the opponent's two views and same own reply, and
has a different own information-history hash. No alternative is inserted
into our posterior or assigned a counterfactual probability. The 7,229
alternatives overlap hypotheses and games; they are not independent tactics
or a win-rate sample.

## What the implementation retains

Before committing our move, the extension transfers ownership of the existing
position/history/weight arrays into a shared ancestor pool. Current worlds
carry an 8-byte origin containing its parent index, hypothesized opponent
reply and validity state. Origins follow every thread concatenation, cap
selection and shrink compaction. The next own move replaces the old pool.
Recovery disables natural ancestry; the test does not pretend invented
placements have a witnessed past. One representative history survives a
native merge, matching the baseline's choice; this is not exhaustive history
tracking.

The extension is opt-in through a C API. No release source, model, guard,
solver, search policy or published ZIP changes. The actor has no replay or
true-board reader. Its native opponent move model and public history table
are unchanged.

## Boundaries before search integration

- These are the same 32 development root selections used by the oracle
  screens, not fresh confirmation. Only the input interface has changed.
- The fixed shrink-to-4,096 schedule after opponent updates makes state
  parity meaningful and bounds this screen. The measured 0.7% CPU overhead
  is descriptive here, not an arena overhead guarantee or whole-turn speedup.
- The producer certifies **two-step local legality**, metadata and views.
  Complete native-path repetition counts are not retained, so draw-history
  certification remains open. The full native path is represented by hashes
  and the baseline filter, not an independently reconstructed move transcript.
- No tactical reply-vector advantage, opponent exploit, better root action
  or game result is measured in this screen.
- Alternative reach probabilities, previous blueprint policies, continuation
  values and correct own-information-set partitioning remain undefined. Raw
  alias counts and native posterior log-weights are not those probabilities.
  Blindly appending alternatives to the deployed single-own-root search
  would fuse distinct private decisions and solve the wrong game.

Passing earns a separate reference-reach and information-set integration
design review. Existing M4 already implements carry/gadgets and has negative
match evidence; this producer is a distinct source of fresh alternatives,
not a claim that M4 is new. No automatic match batch, fourth oracle screen,
release number or arena upload follows.

## Reproduction and retained failures

Source and the 81-hash plan were pushed and verified on both mirrors at
`7a024ab8c79b93fc3ed88a33275aa161fa605a8d` before collection. Original run
session `16866` exited 0 after 7.483 seconds, completing all 96 first attempts.
Original independent auditor session `26095` exited 0; its audit took 3.637
seconds. Neither process remains live, as verified by host `/proc` checks.

The initial synthetic capture fixture incorrectly moved Kh8-g8 onto the Bd5
diagonal. Its failed preflight and diagnostic are preserved; Kh8-h7 corrects
the fixture before collection. A sandbox LeakSanitizer ptrace error is also
preserved. Running the same sanitizer binary outside that monitor passes
address, undefined-behavior and leak checks. Units cover EP in both colors,
castling both wings/colors, promotion, underpromotion, captures, cap, shrink,
pool replacement and recovery exclusion. No frozen prefix was restarted.

- [Plan](plan.json), [preflight](preflight.json), [completion](completion.json),
  [independent audit](audit.json), [host cleanup](cleanup.json).
- [Native corpus manifest](corpus-manifest.json),
  [all 740 exported contexts and their alternatives](native-contexts.jsonl.gz).
- [Source and tests](../../experiments/private-ancestry-20261110/),
  [original design](../../next-private-ancestry-design-20261110.md),
  [prior-work register](../../RESEARCH_REGISTER.md).

All 4,725,746 bytes of raw outputs plus exact private actor inputs and process
receipts remain under the authorized Seagate directory
`iamavirus/astra/private-ancestry-20261110/`. Its manifest records compressed
corpus hashes and the uncompressed hash. No GPU or model fit was needed.
