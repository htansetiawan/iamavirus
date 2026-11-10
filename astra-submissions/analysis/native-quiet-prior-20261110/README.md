# Native fixed full-prior correctness — passed

The isolated adapter reproduces the previously validated293 C head and
unchanged native zero behavior. It is not a cost, posterior or strength result.
Source/check plan00a11c6d was verified on both mirrors before original tool
93219; it exits0 in40.95seconds. Cores2–3 are released. No API,GPU,failed-disk
access, fit, Fable source edit or arena/version/ZIP action.

64reused TRAIN games:5,419states,1,438selected contexts,47,110candidate actions
match original moves/features/history. Learned logp has zero maximum error
versus the original293 C implementation. Zero-head entries and capture
entries are bit-identical, including native history blending/temperature.
Special alternatives include44promotion,118castling and4en-passant moves.

Four full traces, both observer colors:12first original/off/zero executions,
401updates per arm /1,203total. All ordered population/history/float-weight/
RNG fingerprints match, including32cheap-regime opponent updates and2capped
traces. This is fingerprint equality, not separately archived full populations.
The independent raw-row/dependency/bundled-source audit passes. Timing fields
are incidental and are not used to claim overhead or playing performance.

The adapter uses the old global normalizer and returns normalized logp, then
the unchanged updater consumes it with log_z0. Only the full-feature native
regime uses the fixed quadratic head; cheap cutoff/history/temp/cap/guards
are unchanged. Each full feature vector is computed once and reused for
original dot product and quiet residual. No performance backport is included.

`native-source.tar.gz` retains exact original/patched source, generated float32
hex coefficients and helpers. Raw diffs are `.patch.gz`; zero-context `.patch`
companions apply exactly without fuzz. The initial pre-commit whitespace
publication failure is retained; no code/plan/binary or data test changed.

Next: freeze a separate ordinary-cutoff native-cost/sequential-belief study
with the same fixed head. Correctness alone does not show improved truth
support/log share, calibrated guards, equal-clock policy or Elo. The
learned-head updater has not been run on a complete trajectory here.
