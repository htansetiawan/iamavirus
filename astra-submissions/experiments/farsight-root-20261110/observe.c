/* Read-only export AFTER the original decision. No true board or target move. */
#include "observe.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static int frontier(int node, const int *leaf_of, int cap) {
    return node < cap && leaf_of[node] >= 0;
}

void astra_root_observe(const Game *g, const double *x, const MoveList *ours,
                        const Belief *b, const int *idx, const double *share, int K,
                        const int *roots, const int *leaf_of, int leaf_cap) {
    const char *path = getenv("ASTRA_ROOT_OUT");
    if (!path || !*path) return;
    double *v = malloc((size_t)g->n_nodes * sizeof(double));
    if (!v) exit(81);
    /* Nodes append children; verify this instead of assuming traversal order. */
    for (int i = g->n_nodes - 1; i >= 0; --i) {
        const GameNode *n = &g->nodes[i];
        v[i] = n->type == NODE_TERMINAL ? n->value : 0;
        for (int a = 0; a < n->count; ++a) {
            int e = n->first + a, c = g->child[e];
            if (c <= i || c >= g->n_nodes) exit(82);
            double p = n->type == NODE_CHANCE ? g->prob[e] : x[g->is_offset[n->infoset] + a];
            v[i] += p * v[c];
        }
    }
    FILE *f = fopen(path, "wx");
    if (!f) exit(83);
    fprintf(f, "{\"count\":%zu,\"us\":%d,\"temperature\":%.17g,\"root_value\":%.17g,\"worlds\":[",
            b->count, b->us, belief_temperature(), v[g->root]);
    for (size_t i = 0; i < b->count; ++i) {
        const Position *p = &b->items[i]; char board[65]; pos_to_board_string(p, board);
        fprintf(f, "%s{\"index\":%zu,\"board\":\"%s\",\"logw\":%.9g,\"side\":%d,"
                "\"castle\":\"%016" PRIx64 "\",\"ep\":%d,\"halfmove\":%d,\"hist\":\"%016" PRIx64 "\"}",
                i ? "," : "", i, board, b->logw ? (double)b->logw[i] : 0, p->side,
                p->castle_rooks, p->ep, p->halfmove, b->hist ? b->hist[i] : 0);
    }
    fputs("],\"samples\":[", f);
    for (int k = 0; k < K; ++k) {
        fprintf(f, "%s{\"index\":%d,\"weight\":%.17g,\"actions\":[", k ? "," : "", idx[k], share[k]);
        const GameNode *root = &g->nodes[roots[k]];
        if (root->count != ours->count) exit(84);
        for (int a = 0; a < ours->count; ++a) {
            int child = g->child[root->first + a]; const GameNode *n = &g->nodes[child];
            char uci[6]; move_to_uci(ours->moves[a], uci);
            fprintf(f, "%s{\"move\":\"%s\",\"value\":%.17g,\"type\":%d,\"frontier\":%s,\"replies\":[",
                    a ? "," : "", uci, v[child], n->type, frontier(child, leaf_of, leaf_cap) ? "true" : "false");
            if (n->type == NODE_PLAYER) {
                Position p = b->items[idx[k]]; Undo undo; make_move(&p, ours->moves[a], &undo);
                MoveList replies; generate_moves(&p, &replies);
                if (n->player != 1 || n->count != replies.count) exit(85);
                for (int j = 0; j < replies.count; ++j) {
                    int reply = g->child[n->first + j]; char text[6]; move_to_uci(replies.moves[j], text);
                    fprintf(f, "%s{\"move\":\"%s\",\"probability\":%.17g,\"value\":%.17g,\"type\":%d,\"frontier\":%s}",
                            j ? "," : "", text, x[g->is_offset[n->infoset] + j], v[reply],
                            g->nodes[reply].type, frontier(reply, leaf_of, leaf_cap) ? "true" : "false");
                }
            }
            fputs("]}", f);
        }
        fputs("]}", f);
    }
    fputs("]}\n", f);
    int failed = ferror(f); failed |= fclose(f) != 0; free(v);
    if (failed) exit(86);
}
