# Private-history continuation feasibility

Experiment 241 implements a data generator, not a playing candidate. The
previous outcome predictor could sharpen a wrong forecast before a real game
reversal. Its inputs did not identify either continuation policy or private
history. This study checks the mechanics and cost of producing outcomes under
explicit policies from restored observation prefixes.

The unmodified course referee runs from the initial board. Each player gets
all its own observations and clocks and is forced through only its own past
actions. At the branch, all future moves are newly generated. The referee's
board, castling, en-passant, halfmove and repetition history are never reset
from FEN. Recorded elapsed time restores historical clocks up to the branch;
afterward actual timed moves spend the remaining clocks normally.

An isolated v37 copy changes replay mechanics only: opt-in continuation after
the first searched move, and restoration of the internal clock after each
forced move. The core engine checkout, weights, search and guard code are not
edited. Existing replay behaviour stays the default.

This restores permitted information, not the old bot's exact internal memory.
Historical searches are skipped, and measured-cost belief thinning/RNG state
can differ. The continuation policy is therefore explicitly the reconstructed
v37 process, not an assertion of what the actual historical player would do.
Player names and the true board are not sent to an actor. Environment clocks,
the referee state and later outcome labels are privileged environment data.

First validate transcript privacy and state restoration, including a threefold
case that a FEN reset would lose. Then freeze two outcome-independent prefixes
and run at most 64 new plies each with v37 capped at one second per move, on an
exclusive core pair. A horizon cutoff is censored, never labelled a draw.
Technical failures stop the run and remain recorded. No retries or fitting.
This measures feasibility/cost at the stated short search budget, not arena
strength or the suitability of these outcomes as arena-budget training labels.
