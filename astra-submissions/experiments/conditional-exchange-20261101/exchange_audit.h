/* Post-choice diagnostics. No hidden truth or counterfactual move enters search. */
#include "numeric_audit.h"

static void exchange_branch(FILE *f, const Tree *t, int id, const Position *p,
                            const double *x, const double *values, int depth) {
    const Game *g = &t->g;
    const GameNode *n = &g->nodes[id];
    char board[65]; pos_to_board_string(p, board);
    fprintf(f, "{\"id\":%d,\"type\":%d,\"infoset\":%d,\"q\":%.17g,"
               "\"stored_value\":%.17g,\"board\":\"%s\",\"side\":%d,"
               "\"castle\":%" PRIu64 ",\"ep\":%d,\"frontier\":%s,\"children\":[",
            id, n->type, n->infoset, values[id], n->value, board, p->side,
            p->castle_rooks, p->ep,
            id < t->cap_leaf_of && t->leaf_of[id] >= 0 ? "true" : "false");
    if (n->type == NODE_PLAYER && depth > 0) {
        MoveList moves; generate_moves(p, &moves); assert(moves.count == n->count);
        assert(n->player == (p->side == t->us ? 0 : 1));
        double check = 0, mass = 0;
        for (int a = 0; a < n->count; ++a) {
            const int child = g->child[n->first + a];
            const double probability = x[g->is_offset[n->infoset] + a];
            char u[6]; move_to_uci(moves.moves[a], u);
            Position q = *p; Undo undo; make_move(&q, moves.moves[a], &undo);
            fprintf(f, "%s{\"move\":\"%s\",\"p\":%.17g,\"node\":", a ? "," : "", u, probability);
            exchange_branch(f, t, child, &q, x, values, depth - 1); fputc('}', f);
            check += probability * values[child]; mass += probability;
        }
        assert(fabs(check - values[id]) < 1e-8 && fabs(mass - 1) < 1e-8);
    }
    fprintf(f, "]}");
}

static int exchange_requested(Move move) {
    const char *list = getenv("ASTRA_EXCHANGE_MOVES");
    if (!list) return 0;
    char u[6]; move_to_uci(move, u);
    while (*list) {
        const char *end = strchr(list, ',');
        size_t size = end ? (size_t)(end - list) : strlen(list);
        if (size == strlen(u) && memcmp(list, u, size) == 0) return 1;
        if (!end) break;
        list = end + 1;
    }
    return 0;
}

static void exchange_audit(const Tree *t, const Belief *b, const int *idx, const double *share,
                           int K, int root_I, const MoveList *moves, const SearchResult *out,
                           const double *x) {
    const char *path = getenv("ASTRA_EXCHANGE_OUT"); if (!path) return;
    const uint64_t original_hash = audit_tree_hash(&t->g);
    double *values = malloc(t->g.n_nodes * sizeof(*values));
    unsigned char *marks = calloc(t->g.n_nodes, 1); assert(values && marks);
    double value = audit_value(&t->g, t->g.root, x, values, marks);
    assert(fabs(value - out->value) < 1e-8);
    FILE *f = fopen(path, "wx"); assert(f);
    char selected[6]; move_to_uci(out->move, selected);
    fprintf(f, "{\"selected\":\"%s\",\"value\":%.17g,\"nodes\":%d,"
               "\"belief_count\":%zu,\"us\":%d,\"marginal_order\":\"PNBRQKpnbrqk\",\"marginals\":[",
            selected, value, t->g.n_nodes, b->count, b->us);
    double marginals[12][64] = {{0}}, total = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const double w = b->logw ? exp((double)b->logw[i]) : 1;
        total += w;
        for (int s = 0; s < 64; ++s)
            if (b->items[i].piece[s] != NO_PIECE)
                marginals[6*b->items[i].color[s]+b->items[i].piece[s]][s] += w;
    }
    assert(total > 0);
    for (int p = 0; p < 12; ++p) {
        fprintf(f, "%s[", p ? "," : "");
        for (int s = 0; s < 64; ++s) fprintf(f, "%s%.17g", s ? "," : "", marginals[p][s]/total);
        fputc(']', f);
    }
    fprintf(f, "],\"actions\":[");
    const GameNode *root = &t->g.nodes[t->g.root];
    for (int a = 0; a < moves->count; ++a) {
        double q = 0; char u[6]; move_to_uci(moves->moves[a], u);
        for (int k = 0; k < K; ++k) {
            const GameNode *world = &t->g.nodes[t->g.child[root->first+k]];
            q += share[k] * values[t->g.child[world->first+a]];
        }
        fprintf(f, "%s{\"move\":\"%s\",\"p\":%.17g,\"q\":%.17g}",
                a ? "," : "", u, x[t->g.is_offset[root_I]+a], q);
    }
    fprintf(f, "],\"worlds\":[");
    for (int k = 0; k < K; ++k) {
        const Position *p = &b->items[idx[k]]; char board[65]; pos_to_board_string(p, board);
        const GameNode *world = &t->g.nodes[t->g.child[root->first+k]];
        fprintf(f, "%s{\"weight\":%.17g,\"board\":\"%s\",\"side\":%d,\"castle\":%" PRIu64 ",\"ep\":%d,\"branches\":[",
                k ? "," : "", share[k], board, p->side, p->castle_rooks, p->ep);
        MoveList legal; generate_moves(p, &legal); int written = 0;
        for (int a = 0; a < moves->count; ++a) {
            if (!exchange_requested(moves->moves[a])) continue;
            assert(has_move(&legal, moves->moves[a]));
            Position q = *p; Undo undo; make_move(&q, moves->moves[a], &undo);
            char u[6]; move_to_uci(moves->moves[a], u);
            fprintf(f, "%s{\"move\":\"%s\",\"node\":", written++ ? "," : "", u);
            exchange_branch(f, t, t->g.child[world->first+a], &q, x, values, 2);
            fputc('}', f);
        }
        fprintf(f, "]}");
    }
    fprintf(f, "],\"tree_hash\":\"%016" PRIx64 "\",\"post_choice_only\":true}\n", original_hash);
    assert(original_hash == audit_tree_hash(&t->g));
    assert(!ferror(f)); assert(fclose(f) == 0); free(values); free(marks);
}
