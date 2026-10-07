# Interactive system notebook

Public site: <https://htansetiawan.github.io/iamavirus/>

The site is the repository-root `index.html`. It is a self-contained, static
notebook with clickable architecture nodes, a replay and move-lifecycle viewer,
neural-head details, version mappings, and a search-budget calculator. It uses
no live arena API or private credentials. Its arena and research figures are
dated snapshots, not live standings.

## Publishing

The public repository is <https://github.com/htansetiawan/iamavirus>.
`.github/workflows/pages.yml` copies only `index.html` into the Pages artifact.
Pages uses GitHub Actions, with the workflow restricted to this public mirror.

In this shared checkout, `origin` has two push URLs: the source repository and
the public mirror. `git push origin main` updates both. This Git configuration
is local to this checkout; it is not inherited by a fresh clone. The histories
were joined without rewriting either repository's existing commits.

On 2026-10-07, a push and workflow dispatch authenticated as `henryatharvard`
could not start Actions: GitHub returned `Actions has been disabled for this
user`. The mirror owner's account, `htansetiawan`, successfully dispatched the
workflow. Until that account restriction changes, after pushing a site edit,
use **Actions → Publish architecture notebook → Run workflow** on the public
repository while signed in as its owner. Alternatively, use an owner-scoped
CLI credential without changing the shared active login. Do not put tokens in
the repository or site.

After a successful workflow, verify the public URL's HTML against the committed
`index.html` and check the interactive controls. A successful Git push alone is
not proof of a deployed page.

## Verified deployment

- Source commit: `edb24ed9c7de20d8c1494e3c4b91cc0fa67e7fec`.
- [Successful initial deployment](https://github.com/htansetiawan/iamavirus/actions/runs/37695703037), completed 2026-10-07 22:22:19 UTC.
- Public HTML matched the local file byte for byte, SHA-256
  `c215e349d5edd608b1cafec3a21430053adf088a954cc2443020a0fe40c0e7b5`.
- Live Chrome checks passed for all five sections, architecture nodes, replay
  visibility and terminal frame, neural heads, version selector, matrix
  calculator, deep links, and mobile navigation. No page errors or horizontal
  overflow at 390 px. See `../analysis/site-preview/deployment.json`.
