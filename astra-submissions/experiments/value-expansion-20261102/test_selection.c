/* Exercise the actual patched selection function, including its cache/fallback. */
#include <assert.h>
#include <stdio.h>
#include "build/candidate/src/gtcfr.c"

static void init_tree(Tree *t, int enabled, unsigned seed) {
    memset(t, 0, sizeof(*t)); game_init(&t->g);
    t->value_expansion = enabled; t->rng = seed;
    int I = game_infoset(&t->g, 0, 2);
    int root = game_node(&t->g, NODE_PLAYER, 0, I, 0);
    int children[2] = {game_node(&t->g, NODE_TERMINAL, 0, -1, .5),
                       game_node(&t->g, NODE_TERMINAL, 0, -1, -.5)};
    game_children(&t->g, root, children, NULL, 2); game_finalize(&t->g);
    ensure_visits(t);
    t->cap_leaf_of = t->g.n_nodes; t->leaf_of = malloc(t->cap_leaf_of * sizeof(int));
    t->leaf_of[root] = -1; t->leaf_of[children[0]] = 0; t->leaf_of[children[1]] = 1;
}

static void drop_tree(Tree *t) {
    free(t->leaf_of); free(t->visits); free(t->moments); expansion_values_free(&t->ev); game_free(&t->g);
}

int main(void) {
    int q_cases = 0, support_cases = 0, fallback_cases = 0;
    for (unsigned seed = 1; seed <= 512; ++seed) {
        Tree base, q, fallback; init_tree(&base, 0, seed); init_tree(&q, 1, seed); init_tree(&fallback, 1, seed);
        const double x[2] = {.1, .9}; refresh_expansion(&q, x);
        const int b = pick_once(&base, 0, x, 2), a = pick_once(&q, 0, x, 2), f = pick_once(&fallback, 0, x, 2);
        assert(f == b); ++fallback_cases;
        if (q.q_scored) { assert(a == 0 && b == 1); ++q_cases; }
        else { assert(a == b); ++support_cases; }
        assert(q.q_visits == 1);
        assert(q.moments[0].count == 3 && q.moments[1].count == 3);
        drop_tree(&base); drop_tree(&q); drop_tree(&fallback);
    }
    assert(q_cases > 0 && support_cases > 0);
    /* Opponent follows the unchanged current strategy, regardless of Q. */
    for (unsigned seed = 1; seed <= 128; ++seed) {
        Tree a,b; init_tree(&a,0,seed);init_tree(&b,1,seed);
        const double x[2]={0,1};refresh_expansion(&b,x);
        assert(pick_once(&a,1,x,2)==1);assert(pick_once(&b,1,x,2)==1);
        assert(b.q_scored==0 && b.q_visits==1);drop_tree(&a);drop_tree(&b);
    }
    printf("{\"q_selection_cases\":%d,\"unchanged_support_cases\":%d,\"fallback_cases\":%d,\"nonexplorer_cases\":128}\n",q_cases,support_cases,fallback_cases);
    return 0;
}
