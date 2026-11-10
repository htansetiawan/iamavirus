# Release-number reuse repair — November 10

The legacy hybrid packager checked only its exact output filename. In a
temporary fixture with an existing `v38-mist-c-allchildren.zip`, it created
`v38-hybrid.zip` and overwrote `v38-manifest.json`. The real release was never
used for that reproduction. [Before receipt](before-reproduction.json).

The repair checks every numbered Astra archive and the major's manifest before
reading release inputs, and again before publication. Plain, candidate and
minor-label names count. An existing manifest is opened exclusively rather
than overwritten. The required Fable+1 rule is retained: an occupied number
causes refusal, never a silent increment or a fabricated Fable release.

Eight regression tests cover alias collisions, archive-only and manifest-only
claims, minor labels, neighboring majors, exact packaged contents, repeat
publication, Fable version drift and plain/candidate Fable names. All pass.

The actual current-tree command `package_release.py --expected-version 38`
correctly refuses before creating a package. The deployed v38 ZIP and its
manifest retain their original hashes; all 114 source/member hashes match.
[Verification](verification.json). The archive audit's two preparation errors
(root-relative paths and the separate Stockfish `src/search.h`) are retained
in [the preparation receipt](audit-preparation-failure.json); final lookup uses
one launcher-verified enclosing prefix and exact complete member paths.

Source: [packager](../../tools/package_release.py),
[tests](../../tools/test_package_release.py),
[read-only verifier](../../tools/verify_release_numbering.py).

No release, arena/model/engine change, API access, GPU use or strength claim.
All 62 teacher and 12 metadata-recovery dependency pins remain unchanged.
Fable's highest archive is still v37; v38 is already published, so there is
currently no unused successor number satisfying the strict +1 rule.
