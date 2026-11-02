/* Exact archived v37 frontier calculation, exposed for offline comparison.
 * Include its static builder; do not duplicate or edit the playing source.
 * Input: id board64 side castle_rooks_hex ep halfmove played_uci.
 * Output includes the child state, both views and all parent action scores.
 */
#include "gtcfr.c"
#include <stdio.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    fow_init();
    if (!sf_start(argv[1])) { fprintf(stderr, "Stockfish initialization failed\n"); return 3; }
    char id[80], board[65], uci[8]; int side, ep, halfmove;
    unsigned long long castle;
    while (scanf("%79s %64s %d %llx %d %d %7s", id, board, &side, &castle, &ep, &halfmove) == 7) {
        Position p;
        if (!pos_from_board_string(&p, board, side, castle, ep)) return 4;
        p.halfmove = halfmove;
        MoveList l; generate_moves(&p, &l);
        int chosen = -1;
        for (int a = 0; a < l.count; ++a) {
            char s[6]; move_to_uci(l.moves[a], s);
            if (!strcmp(s, uci)) chosen = a;
        }
        if (chosen < 0) return 5;
        int cp[256] = {0}, found[256] = {0}, kids[256];
        const int scored = sf_children(&p, &l, cp, found);
        if (!sf_ready()) { fprintf(stderr, "Stockfish stopped at %s\n", id); return 6; }
        Tree t = {0}; game_init(&t.g); t.us = side ^ 1; t.root_loss = -2;
        uint64_t hist[2] = {0, 0};
        int n = build_children_scored(&t, &p, hist, kids, NULL, scored, cp, found);
        if (n != l.count) return 7;
        Position child = p; Undo undo; make_move(&child, l.moves[chosen], &undo);
        char after[65], white[65], black[65];
        pos_to_board_string(&child, after); observation(&child, 0, white); observation(&child, 1, black);
        /* leaf_of is allocated iff some child is an ordinary evaluated leaf. */
        int node = kids[chosen];
        int terminal = node >= t.cap_leaf_of || t.leaf_of[node] < 0;
        printf("{\"id\":\"%s\",\"board\":\"%s\",\"white\":\"%s\",\"black\":\"%s\","
               "\"side\":%d,\"castle\":\"%llx\",\"ep\":%d,\"halfmove\":%d,"
               "\"value\":%.17g,\"terminal\":%d,\"scored\":%d,\"multipv\":%d,\"actions\":[",
               id, after, white, black, child.side, (unsigned long long)child.castle_rooks,
               child.ep, child.halfmove, t.g.nodes[node].value, terminal, scored, sf_multipv());
        for (int a = 0; a < n; ++a) {
            char s[6]; move_to_uci(l.moves[a], s);
            printf("%s{\"move\":\"%s\",\"cp\":%d,\"found\":%d,\"value\":%.17g}",
                   a ? "," : "", s, cp[a], found[a], t.g.nodes[kids[a]].value);
        }
        printf("]}\n"); fflush(stdout);
        free(t.leaves); free(t.leaf_of); free(t.keys); free(t.vals); free(t.visits); game_free(&t.g);
    }
    if (!feof(stdin)) return 8;
    sf_stop(); return 0;
}
