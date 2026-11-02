#define _POSIX_C_SOURCE 199309L
#include "snapshot.h"
#include <math.h>
#include <time.h>

static double seconds(void) {
    struct timespec t; assert(clock_gettime(CLOCK_MONOTONIC, &t) == 0);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    assert(argc == 5 && strlen(argv[2]) == 64 && strlen(argv[3]) == 64);
    fow_init(); zobrist_init();
    Belief b; snapshot_load(&b, argv[1]);
    const size_t parents = b.count;
    const double start = seconds();
    belief_after_opponent(&b, argv[2]);
    const double elapsed = seconds() - start;
    double sum = 0, mass = 0; size_t matches = 0;
    for (size_t i = 0; i < b.count; ++i) {
        char board[65]; pos_to_board_string(&b.items[i], board);
        double w = exp((double)b.logw[i]); sum += w;
        if (strcmp(board, argv[3]) == 0) { mass += w; ++matches; }
    }
    /* Labels and serialization are outside the timed update and cannot enter it. */
    snapshot_save(&b, argv[4]);
    printf("{\"parents\":%zu,\"children\":%zu,\"update_seconds\":%.9g,\"truth_placements\":%zu,\"truth_mass\":%.17g}\n",
           parents, b.count, elapsed, matches, sum > 0 ? mass / sum : 0);
    belief_free(&b);
    return 0;
}
