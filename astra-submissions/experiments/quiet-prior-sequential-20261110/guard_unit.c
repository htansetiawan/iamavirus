#include "belief.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "guard_predicates.h"

static Position bait(int rook_file, int defender) {
    Position p; pos_clear(&p); p.side = WHITE;
    pos_put(&p, 4, WHITE, KING); pos_put(&p, 3, WHITE, QUEEN);
    pos_put(&p, 56, BLACK, KING); pos_put(&p, 56 + rook_file, BLACK, ROOK);
    pos_put(&p, 43, BLACK, PAWN);
    if (defender) pos_put(&p, 46, WHITE, ROOK);
    return p;
}

static void measure(Position *items, float *weights, size_t count, Move move,
                    double k, double q1, double qt) {
    Belief b; memset(&b, 0, sizeof(b)); b.items = items; b.logw = weights; b.count = count;
    double k1, kt, a, z;
    king_risks(&b, move, 20000, 2., &k1, &kt);
    queen_risks(&b, move, 20000, 2., 4, &a, &z);
    assert(fabs(k1 - k) < 1e-7 && fabs(kt - k) < 1e-7);
    assert(fabs(a - q1) < 1e-7 && fabs(z - qt) < 1e-7);
}

int main(void) {
    fow_init();
    Position p = bait(3, 0); float zero = 0;
    measure(&p, &zero, 1, MAKE_MOVE(3, 43, NO_PIECE), 0, 1, 1);  /* Qxd6, rook takes: 9-1=8 */
    p = bait(3, 1);
    measure(&p, &zero, 1, MAKE_MOVE(3, 43, NO_PIECE), 0, 0, 0);  /* rook recaptures: 9-5-1=3 */
    p = bait(4, 0);
    measure(&p, &zero, 1, MAKE_MOVE(4, 12, NO_PIECE), 1, 0, 0);  /* Ke2 exposed on e-file */
    p = bait(3, 0);
    measure(&p, &zero, 1, MAKE_MOVE(4, 5, NO_PIECE), 0, 0, 0);
    Position worlds[2] = {bait(2, 0), bait(3, 0)};
    float weights[2] = {0, logf(.25f)};
    measure(worlds, weights, 2, MAKE_MOVE(3, 43, NO_PIECE), 0, 1. / 3., .2);
    puts("{\"passed\":true,\"native_guard_cases\":5,\"weighted_fitted_and_tempered\":true}");
    return 0;
}
