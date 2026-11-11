# V38 release records and current state

The reviewed v38 ZIP and manifest are already published in repository main.
The current API still identifies **arena v38** as active. There is no new
release, rebuild, upload, activation or version reservation in this review.

## Two dated public snapshots

| Read | Elo / rank | V38 W–D–L / games | Scope |
|---|---|---|---|
| November 11, 5:01 p.m. Boston (22:01 UTC) | 1986.82 / 8 among visible rated teams | 437–30–306 / 773 | Leaderboard and version metadata agree |
| November 11, 5:06 p.m. Boston (22:06 UTC) | Not fetched for this snapshot | 438–30–306 / 774 | Complete fixed-cursor game listing; one additional win |

The metadata score is 58.47%. The later listing has 431 wins labelled `King capturable`,
six opponent time-forfeit wins and one opponent response-failure win; all
306 losses are `King capturable`. Draws are 28 threefold repetitions and
two fifty-move draws. No diagnostics were fetched; these are the listing's
termination reasons. The separate snapshots must not be presented as one
atomic rating-and-games read. These observations do not estimate a causal
Elo gain over the previous bot.

Ten HTTP requests completed without retries: two metadata reads and eight
sequential listing pages, with the existing client's >=1-second pacing.
Full original JSON responses/receipts remain in the local cache. The public
[arena summary](checked/arena-summary.json) is an explicitly reduced projection,
with hashes/timestamps for its original sources.

### Matchups behind the aggregate rating

The same listing, grouped by opponent ID and **played** version, gives:

| Opponent | Active version at metadata read | V38 record against that version | Score |
|---|---:|---|---:|
| Greek Gift | 27 | No completed matchup; v25 was 2–0–28 | Unknown for v27 |
| Farsight | 29 | 2–0–8 | 20.0% |
| Knight Vision | 36 | 20–3–19 | 51.2% |
| Strongly Invisible | 41 | 9–2–17 | 35.7% |
| Crimson Fog | 4 | 8–0–14 | 36.4% |
| Decent Chess Bot | 7 | 8–3–21 | 29.7% |
| duck | 11 | 6–6–22 | 26.5% |

These are descriptive records with small/differently timed cells, not a
ranking of causal weaknesses or a new benchmark gate. In particular, pooling
all Farsight versions gives 37.5%, hiding the poorer v29 cell. Greek Gift's
v25 record does not measure its new v27. Names label the report; the grouping
uses IDs/versions and creates no player-name policy rule.
[All visible rated opponents and source hashes](matchups.json) ·
[reducer](../../experiments/release-registry-20261111/matchups.py).
The first reducer inserted empty current-version entries while reading a
defaultdict; its source/output are preserved. A non-mutating lookup removes
only those zero-game entries, leaving every total, score and current-version
record unchanged. Missing matchups remain explicit rather than invented play.

## What is actually in the release

| Item | Verified record |
|---|---|
| Arena number | 38; created November 8 at 16:30:06.998338928 UTC |
| Numbered archive | `iamavirus-v38-mist-c-allchildren.zip`, 84,989,047 bytes |
| Uploaded-name alias | `v38-review.zip`, same local bytes |
| ZIP SHA-256 | `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f` |
| Parent | Fable v37, `41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c` |
| Native source | All 19 C/header files match both parent and commit `f76a09e2f58b1ce89025d7a2e75e3a6ec768c07a` |
| Changed common package files | `run.sh` and `bin/stockfish` |
| Opponent prior/history | Inherited unchanged from v37; includes the 359,889-record history table |
| Repository publication | ZIP and manifest Git object IDs match main commit `3e4d2fc9b1b5539e8932da40e8c0f4c6d6a091e9`, independently observed with `git ls-remote` |

All **114 manifest member hashes** verify. The extra embedded release metadata
still says candidate; it was intentionally preserved when the human approved
the experimental arena trial. The external release note/manifest record the
later decision. The two shared registry rows already map this archive to v38
and were left unchanged.

The arena API does not expose uploaded ZIP hashes. The bytes-to-arena mapping
still relies on Henry's upload statement and Fable's same-bytes decision;
the repository-content verification does not supply a remote arena checksum.
The failed local Misty gate and observational nature of retention remain
recorded in [the release note](../../v38-release.md).

Fable's highest physical archive remains v37. The existing packager therefore
requires v38 and refuses it because Astra already occupies that major. This
is the guard repaired in 329, not a new discovery or code change. No suffix,
manifest overwrite, silent bump to v39 or artificial Fable archive was created.

## Documentation corrected

The Astra overview no longer says the daily refresh is running or that its
current episode export is still from November 2. It links the verified
November 11 export and later 68-game canonical import, and distinguishes
offline data products from frozen shipped model coefficients. The historical
README tail and every previous release-note paragraph remain intact.

The first auditor completed its package/public-object checks. Its exact source
and result are retained. The follow-up adds independent reconstruction of
the cached page filters/cursor chain, player/played-version selection, W–D–L
and termination reasons; it does not trust only the collector's totals. Both
audits use the same saved inputs and leave archive/manifest bytes unchanged.
The unused intermediate assignment was also removed from the tool.

[Checked audit](checked/audit.json) · [initial audit](audit.json) ·
[documentation preservation](documentation-review.json) ·
[auditor source](../../tools/audit_release_registry.py).
The complete source audit can be rerun locally with the cached responses and
a fresh `--output` directory. It needs that cache and the parent/source Git
objects; the reduced public summary alone is not the complete input.
No model fit, GPU, bot game, timer/service or website deployment changed.
