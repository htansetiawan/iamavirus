# Presentation repository checkpoint

Prepared on an isolated branch based on e55cd536 for draft human review.
Start at [the review packet](../../review-20261111.md). Website publishing
remains disabled; the shipped v38 archive and manifest remain unchanged.

[Manifest](manifest.json) records selected payload hashes.
[Validation](validation.json) records the isolated 24-page render, 423
source-target checks, 35 Python syntax checks and a fresh read-only audit of
all 114 v38 manifest members. The two-page PDF is included. HTML sibling
links are site navigation; the entry point uses Markdown source links.

[The initial link check](initial-link-check.json) caught six omitted evidence
links; their three existing directories were added before publication.
Generated SVG and frozen unified-diff whitespace is preserved to keep the
original evidence hashes. Every other changed file passes the whitespace
check; both SVGs parse as XML. Generated CFR build copies were excluded.
The preflight corrections and their actual scopes are recorded in validation.

The packet preserves failed playing gates, observational qualifications and
human review pending. It includes evidence summaries and review tooling,
not raw replay datasets, training checkpoints or a new bot release. The
source ledger additions are append-only Astra entries. Shared queues,
core reservations, shared engine code and deployment workflows are outside
the checkpoint. Publication status and PR URL will be recorded separately
after the remote branch is verified.
