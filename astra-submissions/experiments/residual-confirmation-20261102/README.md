# Fresh confirmation of the frozen 239 flat residual

No fitting or model selection here. Experiment239 chose the flat residual
at epoch3 using development validation. That exact checkpoint/payload is the
primary candidate. Query is a frozen secondary comparator; it cannot replace
the primary after seeing results.

Select up to2,000 hash-chosen unused games from10–30October plus up to500
new2November games from the completed bounded600-game public refresh. Both
players must belong to the same pinned top12 cohort as237. Exclude all237/238
games, full trajectories, and canonical input states (including pilots), then
deduplicate across the two new cohorts. Outcome does not affect selection.
Require at least30 new-date source games and1,500 total source games before
extraction; otherwise no test is scored and confirmation remains incomplete.

The older cohort is not prospective or forward-in-time. Pooled equal-game
log loss is primary; the new-date cohort is reported separately and must not
worsen point log loss or Brier. Require at least2% pooled log-loss improvement
over frozen calibratedSF, a whole-game bootstrap95% upper difference below0,
and nonworse pooled Brier. Hidden-threat log loss must not worsen (at least100
positions/30games); ordinary-position log loss must not worsen. Insufficient
subgroups leave the gate incomplete rather than passing it.

Predictions use frozen native FP32 payloads and the exact archived parent
MultiPV baseline. Rule/array/provenance/independent-referee checks must finish
before prediction. No features depend on labels or player identities. This
tests outcome prediction on played positions, not hypothetical search-frontier
calibration or playing strength. Passing earns a separate search-integration
correctness and decision study, followed by full games if justified.
