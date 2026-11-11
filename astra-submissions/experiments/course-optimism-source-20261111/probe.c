/* Three invented utility rounds through the unchanged shipped local learner. */
#include "cfr.h"
#include <stdio.h>

static void vector(const double *v) {
    printf("[%.17g,%.17g,%.17g]", v[0], v[1], v[2]);
}

int main(void) {
    Game g;
    game_init(&g);
    const int I = game_infoset(&g, 0, 3);
    const int root = game_node(&g, NODE_PLAYER, 0, I, 0);
    int children[3];
    for (int a = 0; a < 3; ++a)
        children[a] = game_node(&g, NODE_TERMINAL, 0, -1, 0);
    game_children(&g, root, children, NULL, 3);
    game_finalize(&g);
    const double utilities[3][3] = {{1,0,-1}, {-1,1,0}, {-1,0,1}};
    for (int t = 1; t <= 3; ++t) {
        double before[3], next[3];
        pcfr_current(&g, before);
        for (int a = 0; a < 3; ++a)
            g.nodes[children[a]].value = utilities[t - 1][a];
        pcfr_iteration(&g, t);
        pcfr_current(&g, next);
        printf("{\"round\":%d,\"utility\":", t); vector(utilities[t - 1]);
        printf(",\"strategy\":"); vector(before);
        printf(",\"regret\":"); vector(g.regret);
        printf(",\"last\":"); vector(g.last);
        printf(",\"next\":"); vector(next);
        printf("}\n");
    }
    double average[3];
    pcfr_average(&g, average);
    printf("{\"kind\":\"average\",\"strategy\":"); vector(average); printf("}\n");
    game_free(&g);
    return 0;
}
