# Astra implementation and release rules

- Keep Astra source, analyses, tests, manifests, and ZIPs in this directory. Do not edit Fable's root implementation or `fable-submissions/` as part of an Astra candidate.
- The user requires each new Astra release number to equal the highest major version of a numbered archive in `../fable-submissions/` plus one. Check at packaging and again immediately before publishing. `tools/package_release.py` enforces the packaging rule. Never overwrite a previously published ZIP.
- A repository release and an arena upload are separate actions. Record the actual destination and status. For the current v10 task, the user explicitly authorized publishing the ZIP to the Git repository, not uploading it to the arena.
- Keep the original baseline provenance in `implementation-origin.json`; record changed source/model hashes in each release manifest.
- Run tests appropriate to bot changes and record whether a measurement is a correctness check, an offline replay comparison, or a playing-strength estimate. Do not claim improvement based on a smoke test.
- Coordinate through a new numbered Astra-authored Markdown file in `../chatroom/`. Do not overwrite another author's note. Commit only Astra-owned changes and the relevant chatroom notes; leave unrelated Fable work alone.
