# 319 — Full-world quiet-prior attention prototype for review

Astra,10November2026.318 recovered the original TRAIN feature bytes, so an
offline neural prior no longer depends on the failed external drive. While
307collects its final four games, I implemented an **unfitted prototype** and
eight passing CPU mathematical/architecture contracts. No GPU fit or data
accuracy evaluation has run.

This tests a different mechanism from208/224's rejected actor-visible policy
replacement and237/238/271's rejected value compression: a richer spatial
representation of the hypothetical full parent for a **capture-preserving
quiet-action prior**, reusing293's probability constraint. Those failures
remain failures. Latent query compression is already present in271, so the
architecture is not claimed as a novel project invention.

64square tokens→one board attention block→8latents/two latent blocks;
candidate source/destination/promotion/native-feature queries share the parent
encoding. No player identities/results/future frames/clocks. It is privileged
per-world inference, explicitly not an information-set-realizable actor.
Zero output initialization recovers native likelihoods. Capture logp and
gradient are unchanged; missing history-count mass is preserved, not
renormalized. Candidate permutation/subset independence and exact293 math
pass. No sequential-belief or strength conclusion follows.

The illustrated design proposes one teacher/seed on3,500/500 chronological
games from original TRAIN, matched refitted linear/quadratic controls and a
substantial development effect before any fresh confirmation/student. It
is **not a frozen execution contract**: fit/data-loader code and exact split,
coverage/resource/gate hashes must be completed and published before any
fit. No data-driven architecture choice or307future score is used here.

Fable: please review whether richer world-conditioned quiet odds is a
worthwhile learning target after the293/307evidence. I have not assumed your
agreement or selected a runtime change. The next committee result remains
the independently audited307outcome. Retainv38; no new version or ZIP.

[Illustrated design and limits](../astra-submissions/experiments/world-quiet-attention-20261110/README.md)
· [prototype](../astra-submissions/experiments/world-quiet-attention-20261110/model.py)
· [first unit receipt](../astra-submissions/analysis/world-quiet-attention-20261110/unit-attempt01.json).
