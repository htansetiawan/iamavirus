/* Independent numeric oracle: unequal chance worlds, shared root infoset,
 * zero-probability root action, and an opponent continuation. */
#include "build/src/gtcfr.c"

int main(void) {
    Game g; game_init(&g);
    int root = game_node(&g, NODE_CHANCE, 0, -1, 0);
    int I = game_infoset(&g, 0, 2), J = game_infoset(&g, 1, 2);
    int w[2]; double p[2] = {.25, .75};
    w[0] = game_node(&g, NODE_PLAYER, 0, I, 0);
    w[1] = game_node(&g, NODE_PLAYER, 0, I, 0);
    int a[2] = {game_node(&g, NODE_TERMINAL, 0, -1, 1),
                game_node(&g, NODE_PLAYER, 1, J, 0)};
    int reply[2] = {game_node(&g, NODE_TERMINAL, 0, -1, -2),
                    game_node(&g, NODE_TERMINAL, 0, -1, 2)};
    game_children(&g, a[1], reply, NULL, 2);
    int b[2] = {game_node(&g, NODE_TERMINAL, 0, -1, -.5),
                game_node(&g, NODE_TERMINAL, 0, -1, .4)};
    game_children(&g, w[0], a, NULL, 2); game_children(&g, w[1], b, NULL, 2);
    game_children(&g, root, w, p, 2); game_finalize(&g);
    double x[4] = {1, 0, .25, .75}, values[16]; unsigned char marks[16] = {0};
    double v = audit_value(&g, root, x, values, marks);
    assert(fabs(v - (-.125)) < 1e-12);
    assert(fabs(values[a[1]] - 1) < 1e-12); /* visited even with root probability zero */
    const double qb = .25 * values[a[1]] + .75 * values[b[1]];
    assert(fabs(qb - .55) < 1e-12);
    MoveList moves; moves.count = 2;
    moves.moves[0] = MAKE_MOVE(12, 28, NO_PIECE); moves.moves[1] = MAKE_MOVE(11, 27, NO_PIECE);
    audit_snapshot(stdout, &g, x, I, &moves, 0, 0, x); putchar('\n');
    uint64_t h = audit_tree_hash(&g);
    for (int t = 1; t <= 1000; ++t) pcfr_iteration(&g, t);
    assert(h == audit_tree_hash(&g));
    pcfr_current(&g, x);
    /* Opponent minimizes at its own decision: Q(B)=.25*(-2)+.75*.4=-.2.
       Root therefore selects A at -.125. */
    assert(x[g.is_offset[I]] > .99);
    memset(marks, 0, sizeof(marks));
    assert(fabs(audit_value(&g, root, x, values, marks) - game_value(&g, x)) < 1e-12);
    assert(exploitability(&g, x) < .001);
    /* Structural hashes catch both leaf-value and chance-weight changes. */
    g.nodes[b[1]].value += .1; assert(h != audit_tree_hash(&g));
    g.nodes[b[1]].value -= .1; h = audit_tree_hash(&g);
    g.prob[g.nodes[root].first] += .01; assert(h != audit_tree_hash(&g));
    game_free(&g);

    /* Initial leaf expectation is chance-weighted, not an average of worlds. */
    game_init(&g); root = game_node(&g, NODE_CHANCE, 0, -1, 0); I = game_infoset(&g, 0, 2);
    for (int k = 0; k < 2; ++k) {
        w[k] = game_node(&g, NODE_PLAYER, 0, I, 0);
        int children[2] = {game_node(&g, NODE_TERMINAL, 0, -1, k ? -1 : 1),
                           game_node(&g, NODE_TERMINAL, 0, -1, k ? .5 : 0)};
        game_children(&g, w[k], children, NULL, 2);
    }
    game_children(&g, root, w, p, 2); game_finalize(&g);
    setenv("ASTRA_FROZEN_TREE_OUT", "unused", 1);
    AuditInitial *initial = audit_initial(&g, 2);
    assert(initial && fabs(initial->q[0] + .5) < 1e-12 && fabs(initial->q[1] - .375) < 1e-12);
    free(initial); game_free(&g);
    return 0;
}
