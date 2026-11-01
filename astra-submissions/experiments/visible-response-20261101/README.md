# Visible-board response policy: attention teacher, compact student

1 November 2026. Isolated predictive experiment; no engine or submission change.

The DBR solver is tested, but exact history counts disappear after the opening
in the measured games. Learn a response distribution that generalizes across
positions. Every input is the actor's current 64-square observation and its
legal move list derived from permitted history. No true hidden pieces,
opponent view, player name, result, next observation, or future move enters
the network. The recorded chosen move is a training target only.

This is a memoryless, information-set-realizable policy: indistinguishable
inputs produce one distribution, regardless of the hypothesized true world.
It does not reconstruct all remembered information or claim a complete
opponent belief. Unlike the earlier full-board transition priors, it cannot
read a hidden attacker to decide whether the acting opponent responds to it.

## Frozen design

- Train 4,000 games completed October 20–27; validation 600 on October 28–29;
  test 1,000 on October 30–31. Select by fixed ID hash, without outcomes;
  deduplicate complete move sequences. Exclude the previous temporal-prior
  panel and the 140-game king-calibration panel where their IDs are recorded.
- Target moves of Greek Gift, Knight Vision, Strongly Invisible, Decent Chess
  Bot, Crimson Fog, Instructors, Mist Opportunities, duck and HYPOTHERMIA.
  Both colours, wins and losses; team metadata is for reporting only.
- Canonicalize Black by rank reflection and relative piece colours. Unknown
  and visibly empty have different tokens. Reconstruct legal actions from
  actor observations, castling history and inferred en passant; verify them
  against the independent rules. Stop on a mismatch, never silently discard it.
- Baseline: fitted linear move scorer with piece-specific source/destination
  square tables, target-piece, promotion and geometry features.
- Compact student: visible-board one-hot -> 64 -> 64; concatenate this with
  source/destination tokens, geometry and promotion -> 64 -> one action logit.
- Attention teacher: 64 square tokens, width 128, two four-head transformer
  blocks, feed-forward width 256, dropout .1; mean/source/destination features
  -> 64 -> one action logit. No classification of full true boards.
- Train baseline, direct student and teacher from seed 2081101, AdamW,
  batch 256, up to 12 epochs, weight decay 1e-4; learning rate 1e-3 for
  baseline/student and 3e-4 for teacher. Validate after each epoch; stop a fit
  after three non-improving epochs and retain its best validation checkpoint.
- Train a separate same-sized student from the same initialization with
  `.5 * hard-label CE + .5 * teacher KL at temperature 2 (scaled by 4)`.
  Teacher targets use training inputs only. Same epoch/optimizer limits.
- Choose the student with lower validation NLL after the eighth own move.
  Before test, freeze every model hash and that choice. No architecture or
  seed sweep, no inspecting test to choose a model.

## Gates and resources

Report NLL/top-1 overall and after own move eight, by team and colour, and
pooled Instructors/duck/HYPOTHERMIA. Whole-game bootstrap the chosen student's
paired test NLL gain over the linear baseline. To earn a native-runtime
prototype: validation post-eight gain >= .1 nats, test gain >= .1 with
positive 95% lower bound, and no worse than .01 nats on the reference pool.
A failure stops this architecture/configuration before engine integration;
it does not reject all observation-based modelling. Taxonomy slices are
descriptive and cannot override this gate.

An advancing model must pass Python/native probability parity and a native
CPU cost measurement before a separately frozen DBR decision test. Improved
prediction alone cannot justify an arena ZIP or an Elo claim. Runtime
confidence and query budget have not been selected or tested yet.

GPU is currently free; use it without stopping services, with <=12 GiB
allocated and a 90-minute training wall cap. Two CPU preparation/training
threads, cores 0–1. External storage is unmounted; cap temporary packed data
and checkpoints at 512 MiB on the SSD, preserving compact manifests, hashes,
source and result records. No large general corpus rebuild.
