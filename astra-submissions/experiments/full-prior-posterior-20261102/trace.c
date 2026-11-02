#define _POSIX_C_SOURCE 199309L
#include "belief.h"
#include <assert.h>
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double seconds(void) {
    struct timespec t; assert(clock_gettime(CLOCK_MONOTONIC, &t) == 0);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static Move own_move(const char *uci) {
    assert(strlen(uci) == 4 || strlen(uci) == 5);
    const int from = uci[0] - 'a' + 8 * (uci[1] - '1');
    const int to = uci[2] - 'a' + 8 * (uci[3] - '1');
    assert(from >= 0 && from < 64 && to >= 0 && to < 64);
    int promo = NO_PIECE;
    if (uci[4]) {
        const char *symbols = "nbrq", *which = strchr(symbols, uci[4]); assert(which);
        promo = KNIGHT + (int)(which - symbols);
    }
    return MAKE_MOVE(from, to, promo);
}

int main(int argc, char **argv) {
    assert(argc == 2); FILE *file = fopen(argv[1], "r"); assert(file);
    char line[512], id[16]; int us;
    assert(fgets(line, sizeof line, file) && sscanf(line, "game %15s %d", id, &us) == 2);
    assert(us == WHITE || us == BLACK);
    fow_init(); zobrist_init(); Belief b; belief_init_start(&b, us, 200000);
    int ply = 0, ever_capped = 0;
    while (fgets(line, sizeof line, file)) {
        char who[8], move[8], view[65], board[65]; int side, ep, halfmove; unsigned long long castle;
        assert(sscanf(line, "%7s %7s %64s %64s %d %llx %d %d", who, move, view, board, &side, &castle, &ep, &halfmove) == 8);
        ++ply; assert(side == (ply & 1));
        const size_t parents = b.count;
        const double start = seconds();
        if (b.count) {
            if (strcmp(who, "us") == 0) belief_after_own(&b, own_move(move), view);
            else { assert(strcmp(who, "them") == 0 && strcmp(move, "-") == 0); belief_after_opponent(&b, view); }
        }
        const double elapsed = seconds() - start;
        if (b.overflowed) ever_capped = 1;
        /* Truth is decoded only AFTER the unchanged updater returns. It is a
         * label, never an inserted world, move prior or selection condition. */
        Position truth; assert(pos_from_board_string(&truth, board, side, castle, ep) == 0);
        truth.halfmove = halfmove;
        const uint64_t truth_key = position_key(&truth);
        double total = 0, mass = 0; size_t matches = 0;
        uint64_t sig = history_mix(0x226ULL, b.count), sig2 = history_mix(0xdeadbeefULL, b.count);
        for (size_t i = 0; i < b.count; ++i) {
            const uint64_t key = position_key(&b.items[i]);
            const double w = exp((double)b.logw[i]); total += w;
            if (key == truth_key) { mass += w; ++matches; }
            uint32_t bits; memcpy(&bits, &b.logw[i], sizeof bits);
            const uint64_t fields[4] = {key, b.hist[i], bits, (uint64_t)b.items[i].halfmove};
            for (int k = 0; k < 4; ++k) { sig = history_mix(sig, fields[k]); sig2 = history_mix(sig2, fields[3 - k]); }
        }
        sig = history_mix(history_mix(sig, b.rng), b.last_own);
        sig2 = history_mix(history_mix(sig2, b.overflowed), b.cap);
        printf("{\"ply\":%d,\"decision\":%s,\"parents\":%zu,\"worlds\":%zu,\"ever_capped\":%s,\"matches\":%zu,\"truth_share\":%.17g,\"update_seconds\":%.9g,\"signature\":\"%016" PRIx64 "%016" PRIx64 "\"}\n",
            ply, side == us ? "true" : "false", parents, b.count, ever_capped ? "true" : "false", matches,
            total > 0 ? mass / total : 0, elapsed, sig, sig2);
        fflush(stdout);
    }
    assert(fclose(file) == 0); belief_free(&b);
    return 0;
}
