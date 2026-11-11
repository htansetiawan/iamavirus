/* Teaching fixture linked to the unchanged cfr.c/h from the v38 ZIP.
 * This is a tiny invented game, not a FoW position or a playing experiment.
 * Chance selects W0/W1. Player 0 cannot distinguish the worlds. Player 1
 * knows the world but cannot see player 0's action. Thus I is shared over
 * worlds and J[w] is shared over the two hidden player-0 actions.
 */
#include "cfr.h"
#include <stdio.h>

static void array(const double *v, int n) {
    putchar('[');
    for (int i = 0; i < n; ++i) printf("%s%.17g", i ? "," : "", v[i]);
    putchar(']');
}

static void record(const Game *g, int iteration) {
    double x[6], average[6];
    pcfr_current(g, x);
    pcfr_average(g, average);
    printf("{\"iteration\":%d,\"nodes\":%d,\"infosets\":%d,\"regret\":", iteration, g->n_nodes, g->n_infosets);
    array(g->regret, 6);
    printf(",\"last_instantaneous_regret\":"); array(g->last, 6);
    printf(",\"current\":"); array(x, 6);
    printf(",\"average\":"); array(average, 6);
    printf(",\"strategy_sum\":"); array(g->strategy_sum, 6);
    printf(",\"value\":%.17g,\"solver_exploitability\":%.17g}\n", game_value(g, x), exploitability(g, x));
}

int main(void) {
    const double payoff[2][2][2] = {{{.6, -.2}, {-.4, .4}}, {{-1., .6}, {.6, -.2}}};
    const double probability[2] = {.75, .25};
    Game g;
    game_init(&g);
    const int I = game_infoset(&g, 0, 2);
    const int J[2] = {game_infoset(&g, 1, 2), game_infoset(&g, 1, 2)};
    const int root = game_node(&g, NODE_CHANCE, 0, -1, 0.);
    int worlds[2];
    for (int w = 0; w < 2; ++w) {
        worlds[w] = game_node(&g, NODE_PLAYER, 0, I, 0.);
        int actions[2];
        for (int a = 0; a < 2; ++a) {
            actions[a] = game_node(&g, NODE_PLAYER, 1, J[w], 0.);
            int replies[2];
            for (int b = 0; b < 2; ++b)
                replies[b] = game_node(&g, NODE_TERMINAL, 0, -1, payoff[w][a][b]);
            game_children(&g, actions[a], replies, NULL, 2);
        }
        game_children(&g, worlds[w], actions, NULL, 2);
    }
    game_children(&g, root, worlds, probability, 2);
    game_finalize(&g);
    record(&g, 0);
    for (int iteration = 1; iteration <= 10000; ++iteration) {
        pcfr_iteration(&g, iteration);
        if (iteration <= 5 || iteration == 10 || iteration == 100 || iteration == 1000 || iteration == 10000)
            record(&g, iteration);
    }
    game_free(&g);
    return 0;
}
