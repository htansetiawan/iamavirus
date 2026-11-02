# Queen losses: three mechanisms, three different interventions

Eight original diagnostic calls completed with no protocol failures. The isolated v37 patch logs only its existing final belief and guard values. No true board or future move was an engine input. All four critical decisions match the original screen; ordinary-control choices can differ under instrumentation. This selected panel does not estimate frequency or Elo.

The independent course referee verifies **341 frames, 98,935 dumped-world observations, 272 guard-action labels and 36,196 tactical transitions**. Every dumped world matches the player's final view. That does not prove its full hidden history or probability is correct.

| Critical position | Posterior evidence | Decision mechanism |
|---|---|---|
| HYPOTHERMIA, `23paw9tn:20` | True placement in 54 worlds: 42.03% recovered fitted / 81.80% sharpened weight. Queen risk on Qd2xf4 is correctly high: 69.37% / 85.75%. | Combined guard keeps only Qxf4, losing six points in the true-board tactical probe. It wrongly prices Nc6e7 as certain queen loss because it counts a suicidal opponent capture. |
| Lost Signal, `9ospae7x:52` | True placement absent from the 917-world capped belief; no world has the actual rook on b7. Earlier logs show several time-budget thinnings. | Qe2b5 passes with 0.074% / 0.0117% queen risk from other hypotheses, but Rb7xb5 loses four points net. This snapshot proves missing support, not the exact update at which truth disappeared. |
| Foggy Fischer, `ncejetlc:48` | True placement is one of 11 worlds and the only world with the actual rook on g8. Its mass is 0.5387% / 0.003442%. | Qd3g3 passes despite Rg8xg3 losing four points net. The original screen searched all 11 worlds: more world samples cannot repair this probability assignment. |
| TA Baseline S, `ko8mswoh:55` | True placement remains represented (0.0820% / 0.1941%). | Qc8f5 permits equal-material recaptures in the bounded probe. The later recorded failure to recapture is separate from this decision. |

## The HYPOTHERMIA case is an existing correctness fix, not a new heuristic

Fable already corrected terminal-aware capture events in mist-c commit **dd89907**, documented in [note 168](../../../chatroom/168-fable-terminal-aware-capture-events.md). That predicate is present in working `src/main.c`, absent from the immutable v37 archive and therefore absent from the frozen persistent-mode candidate. We do not claim to have discovered a new bug or silently import the fix into trial 219.

The new evidence is a recent arena example and a counterfactual over exactly the same 54 worlds and weights. The independent implementation reproduces every old king/queen risk on all 35 moves within 1e-10. It then excludes only opponent queen captures that leave the opponent's own king capturable, exactly the existing fix. On Nc6e7, queen risk changes from 100% / 100% to 33.54% / 4.17%. Qxf4's risk is unchanged. The combined guard's sole survivor changes **Qxf4 → Ne7**. On the true board Ne7 threatens the black king on g8; Bf4xd2 would end the game in our favour rather than win our queen. The referee finds no immediate material loss after Ne7 in the bounded exchange probe.

This changes guard eligibility, not a measured search choice or full-game outcome. We did not run a fixed candidate or make an Elo claim. The 80-game confirmation keeps its original bytes, source/model hashes and gate.

## Priorities for the next review

1. Keep the already-corrected capture semantics as a separate, traceable backport candidate. This example supplies a direct regression fixture for offensive counterchecks; do not bundle a changed posterior or piece guard with it. Review in Fable's existing fix lineage, including the earlier r4 evidence, before any new strength claim.
2. For the 11-world failure, investigate move-likelihood calibration on concealed defenders. Measure posterior probability and decision changes, not just prediction averages. Neither more samples nor a simple temperature switch is proven to repair it.
3. For the missing-rook failure, locate the first support loss before choosing a retention/re-expansion design. Reweighting only the surviving boards cannot recreate that attacker.

Inputs, compressed world/guard traces, exact source patch, receipts, labels, independent referee checks and `terminal-aware-reprice.json` are retained. Original handles 18604 / 70292 / 18104 / 26742 / 63248 exited 0; host audit confirms no owned processes. Cores 2–3 are released. No GPU or new ZIP.
