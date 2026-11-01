/* Shared-tree chance and private action test. Python supplies independent LPs. */
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "cfr.h"

/* R rows, C columns, two hidden worlds. Column player cannot see row/world. */
int matrix_solve(const double *A, int R, int C, double confidence,
                 const double *q, int iterations, double *out) {
    assert(R <= 16 && C <= 16);
    Game g; game_init(&g);
    const int row = game_infoset(&g, 0, R), col = game_infoset(&g, 1, C);
    const int root = game_node(&g, NODE_CHANCE, 0, -1, 0);
    int worlds[2]; double weights[2] = {.3, .7};
    for (int w = 0; w < 2; ++w) {
        worlds[w] = game_node(&g, NODE_PLAYER, 0, row, 0);
        int kids[16];
        for (int r = 0; r < R; ++r) {
            kids[r] = game_node(&g, NODE_PLAYER, 1, col, 0);
            int leaves[16];
            for (int c = 0; c < C; ++c)
                leaves[c] = game_node(&g, NODE_TERMINAL, 0, -1, A[(w*R+r)*C+c]);
            game_children(&g, kids[r], leaves, NULL, C);
        }
        game_children(&g, worlds[w], kids, NULL, R);
    }
    game_children(&g, root, worlds, weights, 2);
#ifdef RESTRICTED
    game_restrict(&g, col, confidence, q);
#else
    (void)confidence; (void)q;
#endif
    game_finalize(&g);
    for (int t = 1; t <= iterations; ++t) pcfr_iteration(&g, t);
    double x[32]; pcfr_current(&g, x);
    memcpy(out, x, (R+C)*sizeof(double));
    out[R+C] = game_value(&g, x);
    out[R+C+1] = best_response_value(&g, x, 0);
    out[R+C+2] = best_response_value(&g, x, 1);
    memcpy(out+R+C+3, g.regret, (R+C)*sizeof(double));
    memcpy(out+2*(R+C)+3, g.last, (R+C)*sizeof(double));
    memcpy(out+3*(R+C)+3, g.strategy_sum, (R+C)*sizeof(double));
    double avg[32]; pcfr_average(&g, avg);
    memcpy(out+4*(R+C)+3, avg, (R+C)*sizeof(double));
    game_free(&g);
    return 5*(R+C)+3;
}

/* Constraints installed before grow, plus reallocations beyond initial capacities. */
int grow_test(void) {
    Game g; game_init(&g);
    const int root = game_node(&g, NODE_TERMINAL, 0, -1, .3);
    game_finalize(&g);
    int I = game_infoset(&g, 1, 2);
    double q[2] = {.8, .2};
#ifdef RESTRICTED
    game_restrict(&g, I, .5, q);
#endif
    int kids[2] = {game_node(&g, NODE_TERMINAL, 0, -1, 1),
                   game_node(&g, NODE_TERMINAL, 0, -1, -1)};
    game_expand_leaf(&g, root, 1, I, kids, 2);
    for (int k = 0; k < 180; ++k) {
        int j = game_infoset(&g, k&1, 2);
#ifdef RESTRICTED
        if (k%3 == 0) game_restrict(&g, j, 1, q);
#else
        (void)j;
#endif
    }
    game_grow(&g);
    double *x = malloc(g.n_slots*sizeof(double));
    pcfr_average(&g, x);
#ifdef RESTRICTED
    assert(fabs(x[0]-.65) < 1e-12 && fabs(x[1]-.35) < 1e-12);
#endif
    for (int t = 1; t <= 100; ++t) pcfr_iteration(&g, t);
    pcfr_current(&g, x);
    for (int j = 0; j < g.n_infosets; ++j) {
        const int o = g.is_offset[j];
        assert(fabs(x[o]+x[o+1]-1) < 1e-12);
#ifdef RESTRICTED
        if (g.confidence[j] > 0) {
            assert(x[o] >= g.confidence[j]*q[0]-1e-12);
            assert(x[o+1] >= g.confidence[j]*q[1]-1e-12);
        }
#endif
    }
    free(x); game_free(&g); return 1;
}

/* Record solver arrays through reachable tree growth with restrictions off. */
int growth_trace(double *out) {
    Game g; game_init(&g);
    int leaf = game_node(&g, NODE_TERMINAL, 0, -1, .3), used = 0;
    game_finalize(&g);
    for (int stage = 0; stage < 20; ++stage) {
        int I = game_infoset(&g, stage&1, 2);
#ifdef RESTRICTED
        const double q[2] = {.3, .7}; game_restrict(&g, I, 0, q);
#endif
        int kids[2] = {game_node(&g, NODE_TERMINAL, 0, -1, .1*(stage%5)-.2),
                      game_node(&g, NODE_TERMINAL, 0, -1, .25-.03*stage)};
        game_expand_leaf(&g, leaf, stage&1, I, kids, 2);
        game_start_on(&g, I, stage&1); game_grow(&g);
        for (int t = 1; t <= 7; ++t) pcfr_iteration(&g, stage*7+t);
        pcfr_current(&g, out+used); used += g.n_slots;
        memcpy(out+used, g.regret, g.n_slots*sizeof(double)); used += g.n_slots;
        memcpy(out+used, g.last, g.n_slots*sizeof(double)); used += g.n_slots;
        memcpy(out+used, g.strategy_sum, g.n_slots*sizeof(double)); used += g.n_slots;
        leaf = kids[stage&1];
    }
    game_free(&g); return used;
}

#ifdef STANDALONE
int main(void) {
    double A[18] = {0,-1,1,1,0,-1,-1,1,0, 0,-1,1,1,0,-1,-1,1,0};
    double q[3] = {.8,.1,.1}, out[256];
    for (int k = 0; k <= 4; ++k) matrix_solve(A,3,3,.25*k,q,2000,out);
    assert(grow_test()); return 0;
}
#endif
