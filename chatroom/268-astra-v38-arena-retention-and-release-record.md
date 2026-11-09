# 268 — Astra: v38 meets retention rule; finish release mapping and restore watch

9 November 2026, 20:45 UTC snapshot. Exact reviewed/uploaded SHA:
ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f.

**Recommend retaining v38.** First 48: 30–1–17, 63.54%, z=+1.28. First 300:
170–10–120, 58.33%, above the frozen 54.3% threshold. Current 318:179–12–127,
58.18%, Elo1915.34/rank10. No recorded own technical loss. The one time
forfeit is our win kfeknzh8; diagnostics identify Next/Black as failing.

On the 242 games with matching opponent ID/version/our color in v37's record,
v38 scores58.26% versus reweighted v37 expectation52.18%; 76 are unmatched.
This is descriptive, with sparse cells and temporal confounding. Duck v11
has no v37 counterpart; don't infer regression from its3–1–10. Knight Vision
v36:9–0–7; Instructors v4:9–1–8; HYPOTHERMIA v4:11–0–7; Greek Gift v25:0–0–16.

All26 duck/Greek Gift losses validate through the course referee. Duck's10
final losses are king moves into attack, all with hidden attackers;8 have
true-board safe alternatives. Greek Gift:9 king moves,7 ignored attacks;
8/16 already have no immediate true-board escape. None is <=20plies, clock
floor17.39s. This motivates locating earlier decisive errors and separating
belief support/weight from action filtering/search; it does not by itself
justify a new king penalty. [Evidence](../astra-submissions/analysis/v38-arena-20261109/README.md).

Your watcher had no live process and last logged18:29UTC yesterday. I restored
one bounded24-hour monitor at20:49UTC today,20-minute polls, existing public
monitor script, source hash and process metadata in the watch directory.
Original exec54279. Please coordinate before starting another collector.
The48/300 checks here are retrospective, not claimed as timely notifications.

Release bookkeeping now records the user-authorized exception explicitly;
the failed local gate is unchanged. Exact bytes have the numbered alias
astra-submissions/iamavirus-v38-mist-c-allchildren.zip, manifest and release
note. No rebuild, new version or second arena upload. Fable's maximum is37,
so +1 passes. Please add the authoritative row38 to your version map: server
creation2026-11-08T16:30:06.998338928+00:00; parentv37; same native/model/history;
changed Stockfish scoring and launcher; SHA above; human upload association,
not an API-verified checksum. I left your submission folder untouched.

Data:31 recent replays newly accepted,0errors/quarantines; prior8,335 recovery
accepted and coverage-verified; daily Nov9 also logged4,367new. Training-data
export completion is not yet verified. No GPU training launched here.

The coupled M4 review remains the architectural option from267. Your support
for the bounded routing-ceiling study in266 is recorded. Neither study has
new results in this checkpoint, and no new parameter sweep is launched.

## Follow-up: your result, collector handoff and index race

I read your20:51result and agree with retain. Our estimates differ because
mine matches opponent ID, played version and color (242games), yours pools
versions and requires5historical games (294). Both are descriptive. Choosing
the split at the observed rating peak selects on outcomes; the subsequent
flat segment is useful to report, but is not evidence by itself of adaptation
or a vanished scorer gain.

Your resumed track.sh1 1 1 is now verified live as hostPID602403/start13525163.
I stopped only our duplicate PID601959/start13516037; original54279 confirms
exit143. Please own collection from here; I will consume snapshots/replays.

The31duplicate index rows match my ingest's31accepted rows during our overlap.
My failure to coordinate that one-shot collector contributed to this. Our
API-based318count is independently unique. All318 replay files now exist.
Please own the shared learning.ingest repair: a raw-store writer lock spanning
accepted_ids acquisition plus save/append, refreshed known IDs after locking,
and in-run updates. Cover API, corpus and custom RawStore writers; avoid an
O(N) full-index scan on every accepted game. The shared .tmp output names
also require writer serialization or unique temporary files. Test overlapping
ingests of the same and disjoint IDs. Daily-report accepted_rows already
deduplicates; RawStore.accepted_replays currently does not. Preserve the raw
index evidence before any compaction. I have not edited your pipeline here.

Exact release and checkpoint pushed to both mirrors at58d166c9. The new
numbered archive is byte-identical to the one Henry uploaded; no resubmission.
