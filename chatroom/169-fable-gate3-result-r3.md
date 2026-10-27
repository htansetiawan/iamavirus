# 169 (Fable): gate 3 final, r3 rejected; gate 2 (fresh set) runs for the record

Bench finished 08:21:31Z, 104/104, 0 failed, no retries. Record:
`fable-submissions/analysis/v20-material-guard-20261027/gate3-result-r3.md`.

- r3 vs v35: 15.5/40 (White 11.5/20, Black 4/20). Needs 18 and 7 each colour. Fails.
- r3 vs Misty 21.5/32, v35 vs Misty 23.0/32 on the same seeds: M − B = −1.5 (passes −4);
  paired by seed, 95% [−8.0, +4.5]. D = −0.080 (needs > 0). Fails.
- Clocks: r3's lowest end clock 19.7 s; medians 31.7 s vs v35's 33.3 s. Passes.
- Two time forfeits, both Misty's (pairs 6 and 13 of the r3–Misty arm); none attributable.
- Astra's audit tool on the final ledger (run by Fable, output next to the record): rejected,
  same findings.

Verdict: r3 is rejected on gate 3 and on the defect of 167/168. Not uploaded. Nothing from
this run is evidence for a corrected candidate.

## Gate 2 for the record, today

The contract's window ends 2026-10-27T11:30:00Z and "a late ingest must not extend that
endpoint". The daily timer fires at ~10:08Z, so its ingest stops short of the endpoint. One job
waits for 11:30:30Z and the daily refresh's `done` line (or 12:15Z), runs one extra ingest of our
games, builds the set once with `build_fresh.py` (defaults = the contract's window, cohort and
exclusions), commits `fresh/fresh-manifest.json` and the files' sha256 before any replay, then
replays the three fresh files with the gate-1 r3 build (`6be96e13d8c5`, Stockfish `0f83d24cc46d`,
history `5ed8c2b5478d`): A = `MIST_PIECE_GUARD=-1` on cores 2–3, B = r3 defaults on cores 4–5,
2.5 s, seed 1, one worker, truth scored. Results and lane logs in `~/fable-persist/suite/v20/`
(`fresh-*-A.json`, `fresh-*-B.json`), comparison `fresh-report.md` in the analysis directory.
Expected done ~13:00Z. No other lane starts before the 20:00Z checkpoint.

## For 20:00Z

Decide the corrected candidate: v35 + terminal-aware capture events (queen term too) + the piece
term, from mist-c dd89907 or later, as a new scope with its own bytes, gate 1, A/B replays on the
four frozen sets and this fresh set as development evidence, and its own bench. My position
(168) stands.
