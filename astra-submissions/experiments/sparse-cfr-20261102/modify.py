"""Pure source transformation of the pinned 253 workspace implementation."""
def change(s,a,b,n=1):
 assert s.count(a)==n,(a[:80],s.count(a),n)
 return s.replace(a,b)
def patch(c,h):
 h=change(h,'    int allocated_slots, strategy_valid;', '''    int allocated_slots, strategy_valid;
    int sparse_capacity, sparse_count[2];
    unsigned sparse_epoch, *sparse_seen;
    int *sparse_active, *sparse_previous[2];
    unsigned long long sparse_prediction_clears;''')
 c=change(c,'    free(g->pending); free(g->instant);','''    free(g->pending); free(g->instant);
    free(g->sparse_seen); free(g->sparse_active);
    free(g->sparse_previous[0]); free(g->sparse_previous[1]);''')
 marker='static double traverse(const Game *g, int node, int player, double reach_others, const double *x, double *inst) {'
 c=change(c,marker,'''typedef struct {
    unsigned *seen, epoch;
    int *active, count;
} SparseVisit;

static void sparse_storage(Game *g) {
    if (g->sparse_capacity >= g->n_infosets) return;
    const int old = g->sparse_capacity;
    g->sparse_capacity = slot_capacity(g->n_infosets);
    g->sparse_seen = realloc(g->sparse_seen, (size_t)g->sparse_capacity * sizeof(unsigned));
    memset(g->sparse_seen + old, 0, (size_t)(g->sparse_capacity - old) * sizeof(unsigned));
    g->sparse_active = realloc(g->sparse_active, (size_t)g->sparse_capacity * sizeof(int));
    for (int p = 0; p < 2; ++p)
        g->sparse_previous[p] = realloc(g->sparse_previous[p], (size_t)g->sparse_capacity * sizeof(int));
}

static double traverse(const Game *g, int node, int player, double reach_others, const double *x, double *inst, SparseVisit *work) {''')
 c=change(c,'reach_others * p, x, inst);','reach_others * p, x, inst, work);')
 c=change(c,'reach_others * pa, x, inst);','reach_others * pa, x, inst, work);')
 c=change(c,'player, reach_others, x, inst);','player, reach_others, x, inst, work);')
 c=change(c,'    /* Fog of War positions can have over 100 moves:', '''    if (work && work->seen[I] != work->epoch) {
        work->seen[I] = work->epoch;
        work->active[work->count++] = I;
        memset(inst + o, 0, (size_t)g->is_actions[I] * sizeof(double));
    }
    /* Fog of War positions can have over 100 moves:''')
 start=c.index('void pcfr_iteration(Game *g, int t) {');end=c.index('\nstatic double value_of',start)
 c=c[:start]+'''void pcfr_iteration(Game *g, int t) {
    sparse_storage(g);
    double *x = g->strategy, *inst = g->instant;
    if (!g->strategy_valid) {
        pcfr_current(g, x);
        g->sparse_count[0] = g->sparse_count[1] = 0;
        /* Also covers loading a saved state whose predictions are nonzero. */
        for (int I = 0; I < g->n_infosets; ++I) {
            const int o = g->is_offset[I], n = g->is_actions[I];
            int nonzero = 0;
            for (int a = 0; a < n; ++a) nonzero |= g->last[o + a] != 0.0;
            if (nonzero) {
                const int p = g->is_player[I];
                g->sparse_previous[p][g->sparse_count[p]++] = I;
            }
        }
        g->strategy_valid = 1;
    }
    for (int player = 0; player < 2; ++player) {
        if (++g->sparse_epoch == 0) {
            if (g->sparse_capacity) memset(g->sparse_seen, 0, (size_t)g->sparse_capacity * sizeof(unsigned));
            g->sparse_epoch = 1;
        }
        SparseVisit work = {g->sparse_seen, g->sparse_epoch, g->sparse_active, 0};
        traverse(g, g->root, player, 1.0, x, inst, &work);
        /* Preserve every original weighted-average addition before changing
         * any strategy. Avoid the rounding change of delayed aggregation. */
        for (int I = 0; I < g->n_infosets; ++I) {
            if (g->is_player[I] != player) continue;
            const int o = g->is_offset[I], n = g->is_actions[I];
            for (int a = 0; a < n; ++a)
                g->strategy_sum[o + a] += (double)t * x[o + a];
        }
        for (int k = 0; k < g->sparse_count[player]; ++k) {
            const int I = g->sparse_previous[player][k];
            if (g->sparse_seen[I] == work.epoch) continue;
            const int o = g->is_offset[I], n = g->is_actions[I];
            memset(g->last + o, 0, (size_t)n * sizeof(double));
            strategy_of(g, I, x + o);
            ++g->sparse_prediction_clears;
        }
        g->sparse_count[player] = 0;
        for (int k = 0; k < work.count; ++k) {
            const int I = work.active[k], o = g->is_offset[I], n = g->is_actions[I];
            int nonzero = 0;
            for (int a = 0; a < n; ++a) {
                const double r = g->regret[o + a] + inst[o + a];
                g->regret[o + a] = r > 0 ? r : 0;
                g->last[o + a] = inst[o + a];
                nonzero |= inst[o + a] != 0.0;
            }
            strategy_of(g, I, x + o);
            if (nonzero) g->sparse_previous[player][g->sparse_count[player]++] = I;
        }
    }
}
''' +c[end:]
 # Only best-response diagnostics retain this call after replacing iteration.
 c=change(c,'traverse(g, g->root, player, 1.0, x, inst);','traverse(g, g->root, player, 1.0, x, inst, NULL);')
 return c,h
