# Root promotion credit: isolated correctness amendment

The deployed queen-risk helper subtracts the move's captured material from a
possible subsequent queen loss. It omits the promotion increment. For a pawn
that becomes a queen and is captured without recapture, material loss across
those two plies is1, not9. Credit promoted value minus pawn value in `got`;
keep the same threshold, weights, king/capture semantics and search.

The native bridge compares the untouched archived helper with precisely this
amendment. A course-rule material-ledger reference checks synthetic positions
and the already selected pre-cutoff Farsight position. No actor, fitted model,
posterior, root-search rerun, match, GPU, archive or arena change. This does
not incorporate221's separate terminal-capture correction or reopen its
failed playing gate. No correction is merged into Fable's source.

The gzip patch preserves exact context whitespace. A correctness pass would
prove this bounded accounting amendment only, not more strength or a remedy
for the guarded Qg8 net.


**Superseded; do not merge this root-only patch.** It passes its initial17
fixtures but fails two promotion corner cases in the complete-ledger review.
Use the separately tested full accounting amendment in
`../promotion-ledger-20261110/`, and retain this directory as an incomplete
probe. See chatroom310; neither version is a playing candidate.
