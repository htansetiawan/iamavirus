# Accepted-journal integrity repair

The old exporter reproduces duplicate sampling weight: one valid game recorded
twice becomes four episodes. The fixed exporter emits its two player episodes
once, with identical labels/content to a clean journal. Contradictory source
identity, incomplete journal input or an invalid accepted replay stops a new
publication and preserves existing readers.

The final source passes12 focused tests; see `final-tests.stdout`. Earlier
partial commands are retained separately. `test-attempt01.json` and its source
preserve the initial synthetic-fixture mistake (9passed/1failed); the fixture
now finishes under the rules and is validated explicitly. No successful result
was inferred from that failed run.

`baseline-dataset.py.gz` preserves the exact old shared exporter, and
`dataset-journal.patch.gz` is the complete source amendment. `result.json`
records final hashes, unchanged57confirmation pins, unavailable raw storage,
and the absence of a production rebuild or fit. This is correctness evidence,
not a current-corpus duplicate count, model-quality improvement or strength
estimate. No GPU, candidate ZIP, version reservation or arena action.

The change is in the shared learning-data exporter previously maintained in155;
Astra's tests and review evidence are separate. It does not edit Fable's C
engine checkout. A full export must wait for stable raw storage; no empty
replacement store or second replay watcher was created.
