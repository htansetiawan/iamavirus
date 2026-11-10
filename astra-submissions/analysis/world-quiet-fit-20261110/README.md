# World quiet-prior development fit — predictive signal, parity gate failed

Final decision: **close this fixed configuration on CPU/GPU parity; no
advancement**. `final-decision.json` is authoritative. The earlier `result.json`
contains provisional fit metrics before its required independent CPU stage.
Do not interpret that provisional decision as a completed all-stage pass.

Source/planf993c81d was verified on both mirrors before admission. Two host
checks show0%GPU,750MiB and no compute apps; no service stopped. Original
68927exits1 after fit71.60s(exit0) and CPU review9.69s(exit1). All12epochs run
for same-split linear,quadratic,teacher; teacher epoch11 selected on primary
development NLL. Peak Torch GPU allocation771,201,024bytes. All owned cores
and GPU are released. GPU data and livev38 are not changed by the result.

3,500/500chronological whole games from original293 TRAIN only;81,286training
examples,11,654development,8,987primary. Matched linear/quadratic controls
were refitted on the same3,500, with no old validation/test/307 trajectories.
No identities,results,future frames or clocks are network inputs; full board
and both masks are privileged per-world prior inputs, not an actor policy.

Primary NLL native2.656599,linear2.641256,quadratic2.606715,teacher2.507678.
Teacher gains0.148920nats over native and0.099037 over matched quadratic;
game-bootstrap95% versus quadratic[0.086876,0.110626]. All-move gain0.133875;
2,817capture targets and22,469capture actions are unchanged in the same
Torch normalization. All predictive numeric conditions pass. Priority gains
are+0.152225duck,+0.098207Instructors,+0.126830HYPOTHERMIA, with88/73/81games.
These are reused development results, not independent confirmation or Elo.

Required CPU reevaluation stops at teacher maximum per-row logp discrepancy
0.000929832 versus the frozen0.000100000limit. Preserve original stderr,
checkpoints,scores,source and plan. There is no full independent-review pass.
No threshold relaxation, refit, alternate epoch, favorable slice, fresh test
or automatic retry is earned. The numerical portability cause is unresolved;
positive development headroom is retained evidence, not a qualified model.

For the original architecture and failure comparisons see the experiment
README and chatroom319; the predeclared contract/result are in chatroom320.
The separate307prospective quadratic confirmation passed independently and
is the qualified head for native-cost/sequential-posterior design.
