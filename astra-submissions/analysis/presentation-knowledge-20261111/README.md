# A known board, an uncertain opponent

The [teaching page](../../../docs/presentation-knowledge.md) compares the
recorded prefix `d4 c6 Bf4 d5 e3` with constructed `d4 c6 Nc3 d5 e3`.
The histories have identical Black views and own actions at every step,
equal-clock Black protocol strings, and the same 28 legal Black actions
at the final decision. White's histories differ. This concretely explains
why our singleton current belief does not establish common knowledge.

The course referee and pinned independent C++ rules agree on all 12 states,
both views and complete legal-action sets. The actual line matches the
saved replay. Exhaustive full-history enumeration, rather than only position
deduplication, confirms one compatible White history after ply four.

This is constructed explanatory material, not an empirical strength test.
Compatibility does not assign policy reach, an opponent posterior or a useful
new action. No solver change, new search, fit, match, GPU use, candidate or
release follows. Prior M4/ancestry failures are not reopened.

[Plan](plan.json) · [Rules result](result.json) ·
[Auditor](../../tools/audit_presentation_knowledge.py).

Records, identical protocol strings and the previous course-map text remain
under `data/astra-spool/presentation-knowledge-20261111/`. The latter preserves
the historical wording before the local current-state correction. Website
publishing remains disabled.
