/* Isolated learned-response restriction. CFR mathematics is unchanged from
 * the verified experiment 207. Model inputs are only view + legal actions. */
#include <stdio.h>
#include "adapter.h"
#include "response.h"

static double visible_confidence;
static float *visible_weights;
static int visible_initialized, visible_load_failed;

static void visible_config(void) {
    if (visible_initialized) return;
    visible_initialized = 1;
    const char *value = getenv("ASTRA_VISIBLE_CONFIDENCE");
    char *end = NULL;
    if (value) visible_confidence = strtod(value, &end);
    if (!value || end == value || *end || !isfinite(visible_confidence) ||
        visible_confidence <= 0 || visible_confidence > 1) {
        visible_confidence = 0; return;
    }
    const char *path = getenv("ASTRA_VISIBLE_MODEL");
    if (path && *path) visible_weights = astra_response_load(path);
    if (!visible_weights) {
        visible_load_failed = 1;
        fprintf(stderr, "astra_visible: model_load_failed; restrictions disabled\n");
    }
}

static void dbr_install(Tree *t, int I, const Leaf *leaf) {
    visible_config();
    if (t->g.is_player[I] != 1 || !visible_weights) return;
    struct timespec start; clock_gettime(CLOCK_MONOTONIC, &start);
    char view[65]; uint8_t tokens[64]; uint16_t encoded[256];
    MoveList moves; generate_moves(&leaf->pos, &moves);
    observation(&leaf->pos, leaf->pos.side, view);
    if (moves.count != t->g.is_actions[I] || !visible_pack(view, leaf->pos.side, moves.moves, moves.count, tokens, encoded)) {
        ++t->response_failures; t->g.confidence[I] = 0; goto done;
    }
    /* One response distribution per information set. Verify repeated nodes
     * have identical ordered observable inputs before reusing it. */
    uint64_t key = 1469598103934665603ULL;
    for (int s = 0; s < 64; ++s) key = (key ^ tokens[s]) * 1099511628211ULL;
    for (int a = 0; a < moves.count; ++a) key = (key ^ encoded[a]) * 1099511628211ULL;
    key |= 1;
    if (I >= t->response_key_cap) {
        int old = t->response_key_cap, cap = old ? 2*old : 128;
        while (cap <= I) cap *= 2;
        uint64_t *next = realloc(t->response_keys, (size_t)cap*sizeof(uint64_t));
        if (!next) { ++t->response_failures; goto done; }
        t->response_keys = next;
        memset(next+old, 0, (size_t)(cap-old)*sizeof(uint64_t));
        t->response_key_cap = cap;
    }
    if (t->response_keys[I]) {
        ++t->response_reuses;
        if (t->response_keys[I] != key) {
            ++t->response_mismatches;
            t->g.confidence[I] = 0; /* fail closed; diagnostic gate rejects */
        }
        goto done;
    }
    double q[256];
    if (!astra_response_probs(visible_weights, tokens, encoded, moves.count, q)) {
        ++t->response_failures; goto done;
    }
    game_restrict(&t->g, I, visible_confidence, q);
    t->response_keys[I] = key; ++t->response_calls;
done:
    t->response_seconds += seconds_since(&start);
}

static void dbr_reach(const Game *g, int node, const double *x, double reach,
                      int depth, double *coverage, double *confidence, double *visits) {
    const GameNode *n = &g->nodes[node];
    if (n->type == NODE_TERMINAL || reach <= 0) return;
    if (n->type == NODE_PLAYER && n->player == 1 && g->confidence[n->infoset] > 0) {
        *visits += reach;
        if (depth == 2) { *coverage += reach; *confidence += reach*g->confidence[n->infoset]; }
    }
    for (int a = 0; a < n->count; ++a) {
        double p = n->type == NODE_CHANCE ? g->prob[n->first+a] : x[g->is_offset[n->infoset]+a];
        if (p > 0) dbr_reach(g, g->child[n->first+a], x, reach*p, depth+1, coverage, confidence, visits);
    }
}

static void dbr_report(const Tree *t, const double *x) {
    if (visible_confidence <= 0) return;
    int opponent = 0, constrained = 0;
    for (int I = 0; I < t->g.n_infosets; ++I) if (t->g.is_player[I] == 1) {
        ++opponent; constrained += t->g.confidence[I] > 0;
    }
    double coverage = 0, confidence = 0, visits = 0;
    dbr_reach(&t->g, t->g.root, x, 1, 0, &coverage, &confidence, &visits);
    fprintf(stderr, "astra_visible: opponent_sets %d constrained %d first_reply_coverage %.9g first_reply_confidence %.9g expected_model_visits %.9g calls %lu reuses %lu failures %lu mismatches %lu seconds %.9g load_failed %d\n",
            opponent, constrained, coverage, confidence, visits,
            t->response_calls, t->response_reuses, t->response_failures, t->response_mismatches,
            t->response_seconds, visible_load_failed);
}
