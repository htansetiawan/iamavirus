/* Multi-stage private-card game; same rules as the independent Kuhn test. */
#include <string.h>
#include "cfr.h"
static int term(Game *g, double v) { return game_node(g, NODE_TERMINAL, 0, -1, v); }
void kuhn_solve(const double *confidence, const double *q, int iterations, double *out) {
    Game g; game_init(&g);
    /* infosets: player 0 at its first decision and after check-bet; player 1 after check and after bet */
    int p0_first[3], p0_after_cb[3], p1_after_c[3], p1_after_b[3];
    for (int c = 0; c < 3; ++c) {
        p0_first[c] = game_infoset(&g, 0, 2); p0_after_cb[c] = game_infoset(&g, 0, 2);
        p1_after_c[c] = game_infoset(&g, 1, 2); p1_after_b[c] = game_infoset(&g, 1, 2);
    }
    int root = game_node(&g, NODE_CHANCE, 0, -1, 0.0);
    int deals[6]; double probs[6]; int d = 0;
    for (int c0 = 0; c0 < 3; ++c0)
        for (int c1 = 0; c1 < 3; ++c1) {
            if (c0 == c1) continue;
            const double win = c0 > c1 ? 1.0 : -1.0;
            int n0 = game_node(&g, NODE_PLAYER, 0, p0_first[c0], 0);
            /* check */
            int n1c = game_node(&g, NODE_PLAYER, 1, p1_after_c[c1], 0);
            int n0cb = game_node(&g, NODE_PLAYER, 0, p0_after_cb[c0], 0);
            int kids_cb[2] = {term(&g, -1.0), term(&g, 2.0 * win)};          /* fold, call */
            game_children(&g, n0cb, kids_cb, NULL, 2);
            int kids_c[2] = {term(&g, win), n0cb};                              /* check (showdown 1), bet */
            game_children(&g, n1c, kids_c, NULL, 2);
            /* bet */
            int n1b = game_node(&g, NODE_PLAYER, 1, p1_after_b[c1], 0);
            int kids_b[2] = {term(&g, 1.0), term(&g, 2.0 * win)};             /* fold, call */
            game_children(&g, n1b, kids_b, NULL, 2);
            int kids0[2] = {n1c, n1b};
            game_children(&g, n0, kids0, NULL, 2);
            deals[d] = n0; probs[d] = 1.0 / 6.0; ++d;
        }
    game_children(&g, root, deals, probs, 6);
#ifdef RESTRICTED
    for (int I = 0; I < 12; ++I) game_restrict(&g, I, confidence[I], q + 2*I);
#else
    (void)confidence; (void)q;
#endif
    game_finalize(&g);
    for (int t = 1; t <= iterations; ++t) pcfr_iteration(&g, t);
    pcfr_current(&g, out);
    pcfr_average(&g, out+24);
    memcpy(out+48, g.regret, 24*sizeof(double));
    memcpy(out+72, g.last, 24*sizeof(double));
    memcpy(out+96, g.strategy_sum, 24*sizeof(double));
    game_free(&g);
}
