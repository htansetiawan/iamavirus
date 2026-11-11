# 365 — Henry requests stopping IAmAVirus website deployments

Astra, November 11, 03:11 UTC. Henry is receiving failed-deployment emails
and explicitly requested stopping GitHub deployment on IAmAVirus.

The public repository had two publishing paths: legacy branch/Jekyll and
the custom Pages workflow. Their deployments competed; my failed-job retry
also encountered duplicate artifacts. No arena bot or model was changed.

Completed and verified:

- Custom workflow 377887283 is `disabled_manually`.
- Pages build type is `workflow`, disabling the legacy branch auto-trigger.
- No deployment runs are active, queued, waiting or pending.
- The existing published site was not deleted. No new source push was made.

Fable: keep website publishing off. Do not re-enable or dispatch deployment
unless Henry explicitly asks. Documentation can remain in the repository.
This request stops website deployments; it does not authorize cancelling
unrelated data collection or changing the arena submission.

Local before/after receipts: `data/astra-spool/pages-deploy-stop-20261111/`.
This note and ledger message are local; no extra commit/push accompanies them.
