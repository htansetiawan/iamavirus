# Queen guard: complete promotion accounting amendment

Credit our promotion increment in the move's material gain. Credit an opposing
queen-capture promotion in its gain too; if that capturer is recaptured,
deduct the resulting promoted piece's value. With recapture the promotion
increment cancels and the original pawn cost remains, as it should.

The incomplete root-credit probe is retained in `../promotion-credit-20261110/`.
It fixes the original17fixtures but can create a false negative when both
sides promote. This checker compares original, root-only and complete-ledger
helpers against exact course-rule material transactions on21fixtures,
including recapture and the already selected Farsight position.

The amendment changes promotion bookkeeping only. Capture/king-terminal
approximations, thresholds, weights, search and Fable's source stay unchanged.
It is not a playing candidate and does not fix the recorded guarded Qg8 net.
No actor, fit, GPU, broader replay/match gate, release or arena action follows.
