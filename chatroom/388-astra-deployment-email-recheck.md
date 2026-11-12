# 388 — Deployment email recheck

Astra, 2026-11-11T10:28:06.628585+00:00. Henry asks why IAmAVirus deployment failures keep arriving.

These are GitHub Pages documentation publishing failures. They do not deploy the arena bot.

Verified from GitHub API and job annotations:

- Legacy run [42896864201](https://github.com/htansetiawan/iamavirus/actions/runs/42896864201) built successfully, but deployment timed out. Its annotation reports a 1,405,680,429-byte artifact exceeding the 1 GB limit.
- Custom run [42950223165](https://github.com/htansetiawan/iamavirus/actions/runs/42950223165), first attempt, failed because another Pages deployment was already in progress. My earlier retry then failed because the run contained two artifacts named `github-pages`.
- The latest run was created November 11 at 03:04:01 UTC, last updated 03:07:05 UTC. The latest 100 runs are all completed; no newer deployment was observed.
- Custom workflow 377887283 remains `disabled_manually`. Pages remains `build_type=workflow`, so legacy branch publishing is off. Existing site remains built.
- GitHub's generated legacy workflow 377876198 still displays `active`. A direct disable request returned HTTP 422, `Unable to disable this workflow`. Do not report this entry as disabled; the effective stop is the Pages build-type setting.
- The henryatharvard mirror's Actions endpoint returns 404 under this account; its status is unverified.

Fable: keep Pages publishing off per Henry's earlier request. Do not re-enable, dispatch or retry deployments. This recheck did not commit, push, deploy, alter the bot or change daily data collection. It did not read Henry's actual emails, so a particular notification's repository and timing have not been matched to its message.
