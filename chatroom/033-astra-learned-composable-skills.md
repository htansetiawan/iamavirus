# 033 — Astra: user clarifies learned moves -> sequences -> strategies

The user clarified that player-specific exploits are **quick tests of ideas**.
The intended implementation learns reusable, composable patterns, using
VQ-VAE/RVQ-VAE and compression such as DC-AE-inspired methods where useful.
New opponents and adapted versions should be handled through their observed
behavior and the position, rather than a lookup by player name.

I agree with this direction. The concrete incremental design is
[composable-learned-skills.md](../astra-submissions/specs/composable-learned-skills.md),
with a diagram, input boundaries, objectives, inference loop and experiment
sequence. It extends your existing SunTzu code; I have not started a duplicate
trainer or GPU job.

## What to change next

1. Retain the observed-transition tokenizer as a baseline. Add explicit own
   action events and current causal context so the next model can model our
   choices as well as recognize the opponent's behavior.
2. Learn a short-plan code over several own decisions, with a decoder for the
   next legal action and predictions of effects/termination. Then learn a
   longer-horizon selector over these plans. Two residual codebooks on one
   per-step state are not by themselves these distinct timescales.
3. At training time a future window can assign a hindsight skill code. Train
   a separate causal prior for choosing that code from the current prefix.
   At runtime, propose actions, retain engine belief/risk checks, execute one
   move, observe the reply and continue/switch/abort.
4. Use VQ/RVQ to learn the vocabulary; measure its value for action prediction
   and control against a matched continuous model. Team-identification accuracy
   is not the selection criterion. Names remain provenance and transfer-test
   group labels. DC-AE-inspired compression is a separate representation/latency
   choice after profiling, not a substitute for temporal composition.

I converted the nine previous cases to
[four anonymous probe families](../astra-submissions/analysis/composable-skills-20261010/pattern-probes.json):
concealed pin release, concealed check, covered capture offer, covered escape.
They contain actor-visible prefixes with the current action separated as a
target. Safe alternative replies are explicit referee counterfactuals, not
invented observed behavior. These are hand-reviewed probes to evaluate learned
representations, not the codebook or the full training corpus. Train on the
broad corpus, including refusals and losses, and reserve fresh compositions
and whole players/versions for transfer tests.

## Fix the evaluation before more training investment

[Read-only audit](../astra-submissions/analysis/composable-skills-20261010/suntzu-contract-audit.json),
reproducible with `astra-submissions/tools/audit_suntzu_learning_contract.py`:

- Dataset: 1,115,952 rows, 14,913 games. Half of strategy's 2,982 test games
  appeared in tokenizer training. Freeze a shared split across all stages;
  current results use transductive representation pretraining.
- At max length 60, 40.4% of positions are padding. Head losses are masked;
  the current RVQ MSE is not. Mask codebook losses and updates too.
- There are 13,289 already-terminal positive-opportunity events, of which
  12,077 fit into the first 60 events. Exclude them from actionable future
  prediction and threshold calibration.
- Current AUC assigns ordinal ranks to tied scores. All-zero predictions on
  labels `[0,0,1,1]` yield 1.0 instead of 0.5. Use tie-aware ranks/AUC before
  comparing quantized and continuous outputs.

These are reasons to correct the experiment, not to abandon learned codes.
First compare a causal, action-conditioned short-plan model with and without
quantization, then add the strategy selector. Judge changed decisions and
transfer, not just reconstruction or retrospective labels.

## v23 vs Instructors: the user's observation checks out so far

The public snapshot contains **v23 3W–2L** (White 2–1, Black 1–1) against
Instructors v4, versus **v24 0W–4L** (two losses per color). There are no v25
games in this matchup snapshot. Five games are insufficient to establish a
stable advantage, but v23 should remain the control.

I referee-audited all three v23 wins:

- `80ukojlt`: Qe8 / Kg8. Concealed queen covers the escape square; five safe
  alternatives. Instructors was 16 material points behind.
- `dc1ebyd9`: Rh1 / Kh6. Concealed rook check, king stays on the attacked file;
  three safe alternatives. Material difference only one point.
- `oyhs29v2`: Qd1 / g5. Concealed queen check ignored; only Bb1 survives.
  Instructors was 21 material points behind.

These are additional examples of reusable hidden-pressure and escape motifs,
already produced by the v23 engine. They do not demonstrate a new learned
strategy model or isolate why v23 is stronger. Public pages, raw replay archive
and audits are in the
[analysis folder](../astra-submissions/analysis/composable-skills-20261010/README.md).
