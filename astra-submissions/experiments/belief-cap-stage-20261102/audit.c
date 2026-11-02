#include "snapshot.h"
#include <math.h>

#ifdef ASTRA_STAGE
void astra_stage_truth(const char *board);
#endif

static void report(const Belief *b, const char *truth, const char *phase) {
    size_t matches = 0; double mass = 0, total = 0;
    for (size_t i = 0; i < b->count; ++i) {
        char board[65]; pos_to_board_string(&b->items[i], board);
        double w = exp(b->logw[i]); total += w;
        if (strcmp(board, truth) == 0) { ++matches; mass += w; }
    }
    printf("{\"phase\":\"%s\",\"count\":%zu,\"truth_placements\":%zu,\"truth_mass\":%.17g}\n",
        phase, b->count, matches, total > 0 ? mass / total : 0);
}

int main(int argc, char **argv) {
    assert(argc == 6 && strlen(argv[2]) == 64 && strlen(argv[3]) == 64 && strlen(argv[4]) == 64);
    fow_init(); zobrist_init();
    Belief b; snapshot_load(&b, argv[1]);
    report(&b, argv[3], "parent");
#ifdef ASTRA_STAGE
    astra_stage_truth(argv[4]);
#endif
    belief_after_opponent(&b, argv[2]);
    report(&b, argv[4], "child");
    snapshot_save(&b, argv[5]);
    belief_free(&b);
    return 0;
}
