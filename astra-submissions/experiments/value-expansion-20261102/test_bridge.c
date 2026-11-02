#include "expansion_values.h"
#include <stdlib.h>
#include <string.h>

Game *fixture(int seed, int invalid) {
    Game *g = calloc(1, sizeof(Game)); game_init(g);
    const int root = game_node(g, NODE_CHANCE, 0, -1, 0);
    const int own = game_infoset(g, 0, 2);
    int opp[2], later[2][2];
    for (int a = 0; a < 2; ++a) {
        opp[a] = game_infoset(g, 1, 2);
        for (int b = 0; b < 2; ++b)
            later[a][b] = invalid && a ? later[0][b] : game_infoset(g, 0, 2);
    }
    int worlds[2];
    for (int w = 0; w < 2; ++w) {
        worlds[w] = game_node(g, NODE_PLAYER, 0, own, 0);
        int replies[2];
        for (int a = 0; a < 2; ++a) {
            replies[a] = game_node(g, NODE_PLAYER, 1, opp[a], 0);
            int second[2];
            for (int b = 0; b < 2; ++b) {
                second[b] = game_node(g, NODE_PLAYER, 0, later[a][b], 0);
                int leaves[2];
                for (int c = 0; c < 2; ++c) {
                    const double value = ((seed*13 + w*11 + a*7 + b*5 + c*3) % 31 - 20) / 10.0;
                    leaves[c] = game_node(g, NODE_TERMINAL, 0, -1, value);
                }
                game_children(g, second[b], leaves, NULL, 2);
            }
            game_children(g, replies[a], second, NULL, 2);
        }
        game_children(g, worlds[w], replies, NULL, 2);
    }
    double weights[2] = {.3, .7}; game_children(g, root, worlds, weights, 2);
    game_finalize(g); return g;
}

Game *wide_fixture(void) {
    Game *g = calloc(1, sizeof(Game)); game_init(g);
    int I = game_infoset(g, 1, 257);
    int root = game_node(g, NODE_PLAYER, 1, I, 0), children[257];
    for (int a = 0; a < 257; ++a) children[a] = game_node(g, NODE_TERMINAL, 0, -1, (a-128)/128.0);
    game_children(g, root, children, NULL, 257); game_finalize(g); return g;
}

void grow_fixture(Game *g) {
    int node = -1;
    for (int i = 0; i < g->n_nodes; ++i) if (g->nodes[i].type == NODE_TERMINAL) { node = i; break; }
    int I = game_infoset(g, 1, 3), kids[3];
    for (int a = 0; a < 3; ++a) kids[a] = game_node(g, NODE_TERMINAL, 0, -1, .2*a-.1);
    game_expand_leaf(g, node, 1, I, kids, 3); game_grow(g);
}

void drop_fixture(Game *g) { game_free(g); free(g); }
ExpansionValues *new_values(void) { return calloc(1, sizeof(ExpansionValues)); }
void drop_values(ExpansionValues *v) { expansion_values_free(v); free(v); }
