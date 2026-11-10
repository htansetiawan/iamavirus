#define _POSIX_C_SOURCE 199309L
#include "belief.h"
#include <assert.h>
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "guard_predicates.h"

static double seconds(void) {
    struct timespec t; assert(clock_gettime(CLOCK_MONOTONIC, &t) == 0);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static Move action(const char *uci) {
    assert(strlen(uci) == 4 || strlen(uci) == 5);
    const int from = uci[0] - 'a' + 8 * (uci[1] - '1');
    const int to = uci[2] - 'a' + 8 * (uci[3] - '1');
    assert(from >= 0 && from < 64 && to >= 0 && to < 64);
    int promo = NO_PIECE;
    if (uci[4]) {
        const char *symbols = "nbrq", *which = strchr(symbols, uci[4]);
        assert(which); promo = KNIGHT + (int)(which - symbols);
    }
    return MAKE_MOVE(from, to, promo);
}

static int legal(const Position *p, Move move) {
    MoveList moves; generate_moves(p, &moves);
    for (int j = 0; j < moves.count; ++j) if (moves.moves[j] == move) return 1;
    return 0;
}

/* Truth-share target is the native position-key class (board, side, castle,
 * EP), not a full private-history or halfmove posterior. Fingerprints also
 * include representative histories, halfmoves, exact float weights and RNG. */
static void inspect(const Belief *b, uint64_t truth_key, double *share,
                    size_t *matches, uint64_t signature[2]) {
    double total = 0, mass = 0; *matches = 0;
    uint64_t a = history_mix(0x226ULL, b->count), z = history_mix(0xdeadbeefULL, b->count);
    for (size_t i = 0; i < b->count; ++i) {
        const uint64_t key = position_key(&b->items[i]);
        const double weight = exp((double)b->logw[i]); total += weight;
        if (key == truth_key) { mass += weight; ++*matches; }
        uint32_t bits; memcpy(&bits, &b->logw[i], sizeof(bits));
        const uint64_t values[4] = {key, b->hist[i], bits, (uint64_t)b->items[i].halfmove};
        for (int k = 0; k < 4; ++k) { a = history_mix(a, values[k]); z = history_mix(z, values[3 - k]); }
    }
    signature[0] = history_mix(history_mix(a, b->rng), b->last_own);
    signature[1] = history_mix(history_mix(z, b->overflowed), b->cap);
    *share = total > 0 ? mass / total : 0;
}

int main(int argc, char **argv) {
    assert(argc == 3);
    FILE *file = fopen(argv[1], "r"); assert(file);
    char line[512], id[16]; int us;
    assert(fgets(line, sizeof(line), file) && sscanf(line, "game %15s %d", id, &us) == 2);
    assert(us == WHITE || us == BLACK);
    char *end; const uint64_t seed = strtoull(argv[2], &end, 10); assert(!*end && seed);
    fow_init(); zobrist_init(); Belief belief; belief_init_start(&belief, us, 200000);
    /* Explicit sampler state: FOW_SEED changes search, not this native field. */
    belief.rng = seed;
    int ply = 0, ever_capped = 0;
    while (fgets(line, sizeof(line), file)) {
        char who[8], move[8], view[65], board[65], next[8];
        int side, ep, halfmove; unsigned long long castle;
        assert(sscanf(line, "%7s %7s %64s %64s %d %llx %d %d %7s",
                      who, move, view, board, &side, &castle, &ep, &halfmove, next) == 9);
        ++ply; assert(side == (ply & 1));
        const size_t parents = belief.count;
        const int opponent = strcmp(who, "them") == 0;
        const double start = seconds();
        if (belief.count) {
            if (!opponent) { assert(strcmp(who, "us") == 0); belief_after_own(&belief, action(move), view); }
            else { assert(strcmp(move, "-") == 0); belief_after_opponent(&belief, view); }
        }
        const double elapsed = seconds() - start;
        if (belief.overflowed) ever_capped = 1;
        /* Neither replay truth nor next actual own action is passed into the
         * updater. Decode them only for the following read-only diagnostics. */
        Position truth; assert(pos_from_board_string(&truth, board, side, castle, ep) == 0);
        truth.halfmove = halfmove;
        double share; size_t matches; uint64_t before[2], after[2];
        inspect(&belief, position_key(&truth), &share, &matches, before);
        const int applicable = side == us && strcmp(next, "-") != 0;
        int available = 0; size_t bad_moves = 0, examined = 0;
        double predicted[4] = {.5, .5, .5, .5}, labels[4] = {0, 0, 0, 0};
        const double guard_start = seconds();
        if (applicable) {
            const Move selected = action(next); assert(legal(&truth, selected));
            float lw = 0;
            Belief labelled; memset(&labelled, 0, sizeof(labelled));
            labelled.items = &truth; labelled.logw = &lw; labelled.count = 1;
            king_risks(&labelled, selected, 1, 2., &labels[0], &labels[1]);
            queen_risks(&labelled, selected, 1, 2., 4, &labels[2], &labels[3]);
            assert((labels[0] == 0 || labels[0] == 1) && labels[0] == labels[1]);
            assert((labels[2] == 0 || labels[2] == 1) && labels[2] == labels[3]);
            /* A foreign bot's recorded action may not be legal in every
             * strided hypothesis. Do not simulate illegal moves or silently
             * drop such hard examples: record unavailability and fixed .5. */
            const size_t stride = belief.count > 20000 ? (belief.count + 19999) / 20000 : 1;
            for (size_t i = 0; i < belief.count; i += stride) {
                ++examined; if (!legal(&belief.items[i], selected)) ++bad_moves;
            }
            available = belief.count > 0 && !bad_moves;
            if (available) {
                king_risks(&belief, selected, 20000, 2., &predicted[0], &predicted[1]);
                queen_risks(&belief, selected, 20000, 2., 4, &predicted[2], &predicted[3]);
            }
        }
        const double guard_seconds = seconds() - guard_start;
        inspect(&belief, position_key(&truth), &share, &matches, after);
        assert(before[0] == after[0] && before[1] == after[1]);
        printf("{\"ply\":%d,\"decision\":%s,\"parents\":%zu,\"worlds\":%zu,\"full_update\":%s,"
               "\"ever_capped\":%s,\"matches\":%zu,\"truth_share\":%.17g,\"update_seconds\":%.9g,"
               "\"signature\":\"%016" PRIx64 "%016" PRIx64 "\",\"guard_applicable\":%s,"
               "\"guard_available\":%s,\"guard_bad_moves\":%zu,\"guard_boards\":%zu,"
               "\"king1\":%.17g,\"kingt\":%.17g,\"queen1\":%.17g,\"queent\":%.17g,"
               "\"king_label\":%.0f,\"queen_label\":%.0f,\"guard_seconds\":%.9g}\n",
               ply, side == us ? "true" : "false", parents, belief.count,
               opponent && parents > 0 && parents <= 10000 ? "true" : "false",
               ever_capped ? "true" : "false", matches, share, elapsed, before[0], before[1],
               applicable ? "true" : "false", available ? "true" : "false", bad_moves, examined,
               predicted[0], predicted[1], predicted[2], predicted[3], labels[0], labels[2], guard_seconds);
        fflush(stdout);
    }
    assert(fclose(file) == 0); belief_free(&belief);
    return 0;
}
