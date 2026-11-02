#include "snapshot.h"
int main(int argc, char **argv) {
    assert(argc == 2); fow_init(); zobrist_init();
    Belief b; belief_init_start(&b, WHITE, 200000);
    Position p; pos_start(&p); Undo u;
    Move own = MAKE_MOVE(12, 28, NO_PIECE);
    make_move(&p, own, &u);
    char view[65], parent[65], child[65], path[4096];
    observation(&p, WHITE, view); belief_after_own(&b, own, view);
    assert(b.count == 1); pos_to_board_string(&p, parent);
    snprintf(path, sizeof path, "%s/full.txt", argv[1]); snapshot_save(&b, path);
    b.cap = 1;
    snprintf(path, sizeof path, "%s/capped.txt", argv[1]); snapshot_save(&b, path);
    make_move(&p, MAKE_MOVE(62, 45, NO_PIECE), &u);
    observation(&p, WHITE, view); pos_to_board_string(&p, child);
    printf("{\"parent\":\"%s\",\"child\":\"%s\",\"view\":\"%s\"}\n", parent, child, view);
    belief_free(&b); return 0;
}
