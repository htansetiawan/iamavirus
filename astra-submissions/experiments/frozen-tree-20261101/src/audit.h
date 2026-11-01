/* Offline diagnostics: no truth input, and called after choosing out->move.
 * All extra solver work is on the SAME finite game; it is not a clock-matched
 * alternative playing policy. No training target is certified by stability. */
#include <assert.h>
#include <inttypes.h>
#include <stdio.h>

typedef struct { double q[256]; } AuditInitial;

static double audit_value(const Game *g, int id, const double *x, double *values, unsigned char *marks) {
    assert(id >= 0 && id < g->n_nodes);
    if (marks[id] == 2) return values[id];
    assert(marks[id] == 0); marks[id] = 1;
    const GameNode *n = &g->nodes[id]; double value = n->value;
    if (n->type != NODE_TERMINAL) {
        value = 0;
        for (int a = 0; a < n->count; ++a) {
            double p = n->type == NODE_CHANCE ? g->prob[n->first + a] : x[g->is_offset[n->infoset] + a];
            value += p * audit_value(g, g->child[n->first + a], x, values, marks);
        }
    }
    assert(isfinite(value)); values[id] = value; marks[id] = 2; return value;
}

static uint64_t audit_hash_word(uint64_t h, uint64_t v) { return (h ^ v) * UINT64_C(1099511628211); }
static uint64_t audit_tree_hash(const Game *g) {
    uint64_t h = UINT64_C(1469598103934665603);
    for (int i = 0; i < g->n_nodes; ++i) {
        const GameNode *n = &g->nodes[i]; uint64_t bits; memcpy(&bits, &n->value, sizeof(bits));
        h = audit_hash_word(h, (uint32_t)n->type); h = audit_hash_word(h, (uint32_t)n->player);
        h = audit_hash_word(h, (uint32_t)n->infoset); h = audit_hash_word(h, (uint32_t)n->first);
        h = audit_hash_word(h, (uint32_t)n->count); h = audit_hash_word(h, bits);
    }
    for (int i = 0; i < g->n_edges; ++i) {
        h = audit_hash_word(h, (uint32_t)g->child[i]); uint64_t bits; memcpy(&bits, &g->prob[i], sizeof(bits)); h = audit_hash_word(h, bits);
    }
    for (int i = 0; i < g->n_infosets; ++i) {
        h = audit_hash_word(h, (uint32_t)g->is_player[i]); h = audit_hash_word(h, (uint32_t)g->is_offset[i]);
        h = audit_hash_word(h, (uint32_t)g->is_actions[i]);
    }
    return h;
}

static AuditInitial *audit_initial(const Game *g, int actions) {
    if (!getenv("ASTRA_FROZEN_TREE_OUT")) return NULL;
    AuditInitial *initial = calloc(1, sizeof(*initial)); assert(initial);
    const GameNode *root = &g->nodes[g->root]; assert(root->type == NODE_CHANCE);
    for (int k = 0; k < root->count; ++k) {
        const GameNode *world = &g->nodes[g->child[root->first + k]]; assert(world->count == actions);
        for (int a = 0; a < actions; ++a) {
            const GameNode *child = &g->nodes[g->child[world->first + a]];
            assert(child->type == NODE_TERMINAL);
            initial->q[a] += g->prob[root->first + k] * child->value;
        }
    }
    return initial;
}

static void audit_snapshot(FILE *f, const Game *g, const double *x, int root_I, const MoveList *moves,
                           int extra, double elapsed, const double *initial_prob) {
    double *values = malloc(g->n_nodes * sizeof(*values)); unsigned char *marks = calloc(g->n_nodes, 1);
    assert(values && marks);
    const double value = audit_value(g, g->root, x, values, marks);
    assert(fabs(value - game_value(g, x)) < 1e-8);
    const int offset = g->is_offset[root_I]; double q[256] = {0}, expanded[256] = {0};
    const GameNode *root = &g->nodes[g->root];
    for (int k = 0; k < root->count; ++k) {
        const GameNode *world = &g->nodes[g->child[root->first + k]];
        for (int a = 0; a < moves->count; ++a) {
            int child = g->child[world->first + a]; q[a] += g->prob[root->first + k] * values[child];
            if (g->nodes[child].type != NODE_TERMINAL) expanded[a] += g->prob[root->first + k];
        }
    }
    int selected = 0, greedy = 0; double tv = 0, root_v = 0;
    for (int a = 0; a < moves->count; ++a) {
        if (x[offset + a] > x[offset + selected]) selected = a;
        if (q[a] > q[greedy]) greedy = a;
        tv += fabs(x[offset + a] - initial_prob[a]) * .5; root_v += x[offset + a] * q[a];
    }
    assert(fabs(root_v - value) < 1e-8);
    char choice[6], best[6]; move_to_uci(moves->moves[selected], choice); move_to_uci(moves->moves[greedy], best);
    fprintf(f, "%s{\"extra_iterations\":%d,\"elapsed_extra_seconds\":%.9g,\"tree_hash\":\"%016" PRIx64 "\","
               "\"selected\":\"%s\",\"greedy\":\"%s\",\"root_value\":%.17g,\"root_deviation_gain\":%.17g,"
               "\"selected_value_gap\":%.17g,\"root_total_variation\":%.17g,\"actions\":[",
            extra ? "," : "", extra, elapsed, audit_tree_hash(g), choice, best, value,
            q[greedy] - value, q[greedy] - q[selected], tv);
    for (int a = 0; a < moves->count; ++a) {
        char u[6]; move_to_uci(moves->moves[a], u);
        fprintf(f, "%s{\"move\":\"%s\",\"probability\":%.17g,\"q\":%.17g,\"expanded_mass\":%.17g}",
                a ? "," : "", u, x[offset + a], q[a], expanded[a]);
    }
    fprintf(f, "]}"); free(values); free(marks);
}

static void audit_final(Tree *t, const Belief *b, const int *indices, const double *shares, int count,
                        int root_I, const MoveList *moves, const SearchResult *result,
                        const GtcfrParams *params, AuditInitial *initial, int iteration) {
    if (!initial) return;
    const char *path = getenv("ASTRA_FROZEN_TREE_OUT"); FILE *f = fopen(path, "w"); assert(f);
    double *x = malloc(t->g.n_slots * sizeof(*x)); assert(x); pcfr_current(&t->g, x);
    double start_prob[256]; for (int a = 0; a < moves->count; ++a) start_prob[a] = x[t->g.is_offset[root_I] + a];
    char original[6]; move_to_uci(result->move, original);
    fprintf(f, "{\"schema\":1,\"original_solver_move\":\"%s\",\"original_value\":%.17g,"
               "\"us\":%d,\"belief_count\":%zu,\"belief_capped\":%s,\"nodes\":%d,\"slots\":%d,"
               "\"original_iterations\":%d,\"search_budget\":%.17g,\"samples\":[",
            original, result->value, b->us, b->count, b->overflowed ? "true" : "false", t->g.n_nodes, t->g.n_slots,
            result->iterations, params->seconds);
    for (int k = 0; k < count; ++k) {
        const Position *p = &b->items[indices[k]]; char board[65]; pos_to_board_string(p, board);
        fprintf(f, "%s{\"board\":\"%s\",\"side\":%d,\"castle\":%" PRIu64 ",\"ep\":%d,\"weight\":%.17g}",
                k ? "," : "", board, p->side, p->castle_rooks, p->ep, shares[k]);
    }
    fprintf(f, "],\"avoid\":[");
    for (int a = 0; a < params->avoid_count; ++a) {
        char u[6]; move_to_uci(params->avoid[a], u); fprintf(f, "%s\"%s\"", a ? "," : "", u);
    }
    fprintf(f, "],\"initial\":[");
    for (int a = 0; a < moves->count; ++a) {
        char u[6]; move_to_uci(moves->moves[a], u);
        fprintf(f, "%s{\"move\":\"%s\",\"q\":%.17g}", a ? "," : "", u, initial->q[a]);
    }
    fprintf(f, "],\"snapshots\":[");
    const uint64_t hash = audit_tree_hash(&t->g);
    struct timespec began; clock_gettime(CLOCK_MONOTONIC, &began);
    audit_snapshot(f, &t->g, x, root_I, moves, 0, 0, start_prob);
    int extra = 0, previous_snapshot = 0; const int targets[] = {20, 200, 1000};
    for (int stage = 0; stage < 3; ++stage) {
        while (extra < targets[stage] && seconds_since(&began) < 3.0) { pcfr_iteration(&t->g, ++iteration); ++extra; }
        if (extra == previous_snapshot) break;
        pcfr_current(&t->g, x); assert(audit_tree_hash(&t->g) == hash);
        audit_snapshot(f, &t->g, x, root_I, moves, extra, seconds_since(&began), start_prob);
        previous_snapshot = extra;
        if (extra < targets[stage]) break;
    }
    fprintf(f, "],\"diagnostic_only\":true,\"original_choice_preserved\":true}\n");
    assert(!ferror(f)); int closed = fclose(f); assert(closed == 0); free(x); free(initial);
}
