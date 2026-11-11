# Corpus importer: preserve unknown identity

The move-list format identifies a selected color and its opponent, not the
selected player's name or either team's arena ID. The importer previously
invented IAmAVirus for that seat and copied display names into ID fields.

The exact [earlier staged patch](https://github.com/htansetiawan/iamavirus/blob/65fb95e7d0c22a0347a4069adf9323967a65b9e1/astra-submissions/analysis/corpus-attribution-fix-20261111/ingest-attribution.patch)
is now applied to the real importer in the review branch and shared working
copy. New corpus records use `Unknown corpus seat`, keep the known opponent
name, leave unavailable IDs null and retain `corpusSeat` in the replay. The
API ingestion path is unchanged.

The [regression tests](../../tests/test_ingest_corpus_attribution.py) exercise
both real source colors, full 197-frame parity and accepted-journal metadata,
an explicitly named IAmAVirus opponent, and byte preservation for an already
accepted legacy entry. The unpatched importer produces three expected
attribution failures and one passing cache check. The fixed importer passes
all four. [Result](result.json), [baseline XML](baseline.xml),
[fixed XML](fixed.xml). Only temporary raw stores were used.

The test invocation reused the preexisting rules library pinned in the
receipt, by overriding `_native.ensure_built` before loading it; no native
source was rebuilt. The tests can normally be run with:

```sh
python -m pytest -q astra-submissions/tests/test_ingest_corpus_attribution.py
```

This prevents future incorrect guesses. Existing accepted replays and journals
remain immutable, including the 164 legacy imports. Their
[verified replacement metadata](https://github.com/htansetiawan/iamavirus/blob/65fb95e7d0c22a0347a4069adf9323967a65b9e1/astra-submissions/analysis/corpus-metadata-recovery-20261111/README.md)
remains a separate sidecar; this change does not consume it, repair old folds
or refit a model. No arena version or playing-strength claim follows.

The source change is isolated for Fable review. Applying the tested bytes in
the shared working copy does not merge the branch or rewrite the older
verification receipts. Website publishing stays off.
