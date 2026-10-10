# Composable skills: design, probes and current implementation review

The user's clarified direction is **quick exploit experiments -> learned move
vocabulary -> short move sequences -> strategy composition**, generalizing
across players. VQ/RVQ is a candidate for discrete skill representations;
DC-AE-inspired compression is optional and serves the representation budget.

Delivered:

- [Design and execution diagram](../../specs/composable-learned-skills.md):
  causal state/action inputs, distinct temporal levels, hindsight encoder vs
  causal prior, action/effect/termination objectives, closed-loop execution,
  controlled experiments and transfer tests.
- [Pattern probes](pattern-probes.json): nine referee-verified examples grouped
  into four patterns defined by piece roles and relationships, without player
  names in the data. The current demonstrated action is a target, not a policy
  input. Alternative safe replies are explicitly labeled as counterfactuals.
  This is a small interpretability/evaluation fixture set, not learned skills.
- [SunTzu contract audit](suntzu-contract-audit.json): split overlap, padding
  volume, already-terminal opportunity labels, and an AUC tie counterexample.
  It reads the current dataset and source, using no GPU or model training.
- [Public matchup snapshot](instructors-version-snapshot.json): all 127
  completed IAmAVirus/Instructors games returned by two cursor pages with
  unchanged filters, fetched October 10 around 02:04 UTC.
- [Three v23 win audits](v23-instructor-wins-audit.json), with inputs preserved
  in [the compressed replay archive](v23-instructor-replays.tar.gz).

## v23 observation

All comparisons below are against the same Instructors v4. W–D–L:

| Our arena version | White | Black | Total |
| --- | --- | --- | --- |
| v20 | 1–0–4 | 1–0–4 | 2–0–8 |
| v21 | 2–0–5 | 1–1–5 | 3–1–10 |
| v22 | 0–0–1 | 1–0–0 | 1–0–1 |
| **v23** | **2–0–1** | **1–0–1** | **3–0–2** |
| v24 | 0–0–2 | 0–0–2 | 0–0–4 |

No v25 games occur in this snapshot. The v23/v24 samples are small and not
randomized matches; they support preserving v23 as a control, not attributing
a stable Elo gain or a causal mechanism. The version authority maps v23 to
king-only belief fusion on the v20 engine; v24 adds the original replay book.

The three v23 wins all ended against a concealed queen or rook, with a safe
reply available: an escape into Qe8's line (`80ukojlt`), a move along Rh1's
attacked file (`dc1ebyd9`), and an ignored Qd1 check (`oyhs29v2`). The first and
third followed large material leads; the rook example was close in material.
They corroborate the *existence* of these motifs, not a learned plan selector.

## Validation and reproduction

```sh
.venv/bin/python astra-submissions/tools/audit_suntzu_learning_contract.py --output /tmp/suntzu-contract-audit.json
```

The source and dataset hashes are recorded in the audit. The executed audit
reads only data/source and imports NumPy, not PyTorch. The nine probe examples
were checked for unique IDs, causal input/target separation, valid 64-character
views, safe alternative replies, and absence of player names. Their underlying
referee/observation validations are in the preceding top-six analysis.
The three new v23 replays passed move legality, board reconstruction, tactical
view and terminal-outcome checks with the course referee.

Fable received both the user's direction and concrete review findings through
the append-only ledger and [note 033](../../../chatroom/033-astra-learned-composable-skills.md).
No Fable source, training job, GPU allocation or released bot was changed.
