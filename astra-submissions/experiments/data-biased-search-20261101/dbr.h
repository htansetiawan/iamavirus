/* Included after Tree/infoset helpers, in the isolated v37 gtcfr.c only. */
#include <stdio.h>
static double dbr_max(void) {
    static int init = 0;
    static double value = 0;
    if (!init) {
        const char *s = getenv("ASTRA_DBR_MAX");
        if (s) value = atof(s);
        if (!isfinite(value) || value < 0 || value > 1) value = 0;
        init = 1;
    }
    return value;
}

static void dbr_install(Tree *t, int I, const Leaf *leaf) {
    if (t->g.is_player[I] != 1 || dbr_max() <= 0) return;
    MoveList moves;
    generate_moves(&leaf->pos, &moves);
    unsigned counts[256];
    const unsigned N = belief_history_counts(leaf->hist[1], &moves, counts);
    unsigned legal = 0;
    for (int a = 0; a < moves.count; ++a) legal += counts[a];
    if (N < 3 || legal != N || moves.count != t->g.is_actions[I]) return;
    double q[256];
    for (int a = 0; a < moves.count; ++a) q[a] = (double)counts[a] / N;
    game_restrict(&t->g, I, dbr_max() * N / (20.0 + N), q);
}

static void dbr_reach(const Game *g, int node, const double *x, double reach,
                      int depth, double *first_coverage, double *first_confidence,
                      double *model_visits) {
    const GameNode *n = &g->nodes[node];
    if (n->type == NODE_TERMINAL || reach <= 0) return;
    if (n->type == NODE_PLAYER && n->player == 1 && g->confidence[n->infoset] > 0) {
        *model_visits += reach;
        if (depth == 2) {
            *first_coverage += reach;
            *first_confidence += reach * g->confidence[n->infoset];
        }
    }
    for (int a = 0; a < n->count; ++a) {
        const double p = n->type == NODE_CHANCE ? g->prob[n->first+a] : x[g->is_offset[n->infoset]+a];
        if (p > 0) dbr_reach(g, g->child[n->first+a], x, reach*p, depth+1,
                             first_coverage, first_confidence, model_visits);
    }
}

static void dbr_report(const Tree *t, const double *x) {
    if (dbr_max() <= 0) return;
    int opponent = 0, constrained = 0;
    for (int I = 0; I < t->g.n_infosets; ++I) if (t->g.is_player[I] == 1) {
        ++opponent;
        if (t->g.confidence[I] > 0) ++constrained;
    }
    double first = 0, conf = 0, visits = 0;
    dbr_reach(&t->g, t->g.root, x, 1, 0, &first, &conf, &visits);
    fprintf(stderr, "astra_dbr: opponent_sets %d constrained %d first_reply_coverage %.9g first_reply_confidence %.9g expected_model_visits %.9g\n",
            opponent, constrained, first, conf, visits);
}
