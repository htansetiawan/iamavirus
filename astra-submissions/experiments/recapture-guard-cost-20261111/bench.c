/* Component timing harness. The generated prefix supplies both source versions.
 * No referee protocol, belief update, search or Stockfish process is invoked. */
static volatile double bench_sink;

static long long bench_ns(clockid_t clock) {
    struct timespec t; clock_gettime(clock, &t);
    return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}

static double bench_pass(const Belief *b, const MoveList *moves, size_t cap, double temp, int arm, int repeats) {
    double sum = 0;
    for (int r = 0; r < repeats; ++r) {
        /* Prevent reuse across identical passes; no timed counter instrumentation. */
        __asm__ __volatile__("" ::: "memory");
        for (int j = 0; j < moves->count; ++j) {
            double q[3], p[3];
            if (arm) {
                queen_risks(b, moves->moves[j], cap, temp, 4, &q[0], &q[1], &q[2]);
                piece_risks(b, moves->moves[j], cap, temp, 3, 4, &p[0], &p[1], &p[2]);
            } else {
                baseline_queen_risks(b, moves->moves[j], cap, temp, 4, &q[0], &q[1], &q[2]);
                baseline_piece_risks(b, moves->moves[j], cap, temp, 3, 4, &p[0], &p[1], &p[2]);
            }
            sum += q[0] + 2*q[1] + 3*q[2] + 4*p[0] + 5*p[1] + 6*p[2];
        }
    }
    bench_sink = sum;
    return sum;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    const int trace = strcmp(argv[1], "trace") == 0;
    if (!trace && strcmp(argv[1], "time") != 0) return 3;
    FILE *f = fopen(argv[2], "r"); if (!f) return 4;
    size_t n, cap; int us; double temp; char view[65];
    if (fscanf(f, "%zu %zu %d %lf %64s", &n, &cap, &us, &temp, view) != 5 || !n || !cap || temp <= 0) return 5;
    fow_init(); zobrist_init();
    Belief b = {0}; b.count = n; b.us = us;
    b.items = malloc(n * sizeof(Position)); b.logw = malloc(n * sizeof(float));
    if (!b.items || !b.logw) return 6;
    for (size_t i = 0; i < n; ++i) {
        char text[65]; unsigned long long castle; int side, ep, half; double lw;
        if (fscanf(f, "%64s %d %llx %d %d %lf", text, &side, &castle, &ep, &half, &lw) != 6 || side != us) return 7;
        if (pos_from_board_string(&b.items[i], text, side, (bb_t)castle, ep) < 0) return 8;
        b.items[i].halfmove = half; b.logw[i] = (float)lw;
        char seen[65]; observation(&b.items[i], us, seen);
        if (memcmp(seen, view, 64)) return 9;
    }
    char extra[2];
    if (fscanf(f, " %1s", extra) == 1) return 10; /* no trailing input record */
    fclose(f);
    MoveList moves;
    const bb_t home = us == WHITE ? (bb_t)0xff : (bb_t)0xff00000000000000ULL;
    view_moves(view, us, b.items[0].castle_rooks & home, &moves);
    if (moves.count < 1) return 11;
    /* Setup validation is outside timing: every proposed action is legal in every world. */
    for (size_t i = 0; i < n; ++i) {
        MoveList legal; generate_moves(&b.items[i], &legal);
        for (int j = 0; j < moves.count; ++j) {
            int found = 0;
            for (int k = 0; k < legal.count; ++k) if (moves.moves[j] == legal.moves[k]) { found = 1; break; }
            if (!found) return 12;
        }
    }
    const size_t stride = n > cap ? (n + cap - 1) / cap : 1;
    const size_t evaluated = (n + stride - 1) / stride;
    int repeats = (int)((65536 + evaluated * moves.count - 1) / (evaluated * moves.count));
    if (repeats < 1) repeats = 1;
    printf("{\"type\":\"metadata\",\"worlds\":%zu,\"moves\":%d,\"stride\":%zu,\"evaluated\":%zu,\"repeats\":%d}\n", n, moves.count, stride, evaluated, repeats);
    if (trace) {
        const double checksum = bench_pass(&b, &moves, cap, temp, 1, 1);
        printf("{\"type\":\"trace\",\"calls\":%llu,\"scanned_pieces\":%llu,\"attempts\":%llu,\"checksum\":%.17g}\n", bench_calls, bench_scanned, bench_attempts, checksum);
    } else {
        /* Emit the actual component vectors before timing; no root action is selected. */
        for (int j = 0; j < moves.count; ++j) {
            char u[6]; move_to_uci(moves.moves[j], u);
            printf("{\"type\":\"risks\",\"move\":\"%s\",\"arms\":[", u);
            for (int arm = 0; arm < 2; ++arm) {
                double q[3], p[3];
                if (arm) { queen_risks(&b,moves.moves[j],cap,temp,4,&q[0],&q[1],&q[2]); piece_risks(&b,moves.moves[j],cap,temp,3,4,&p[0],&p[1],&p[2]); }
                else { baseline_queen_risks(&b,moves.moves[j],cap,temp,4,&q[0],&q[1],&q[2]); baseline_piece_risks(&b,moves.moves[j],cap,temp,3,4,&p[0],&p[1],&p[2]); }
                printf("%s[%.17g,%.17g,%.17g,%.17g,%.17g,%.17g]", arm ? "," : "",q[0],q[1],q[2],p[0],p[1],p[2]);
            }
            printf("]}\n");
        }
        bench_pass(&b,&moves,cap,temp,0,1); bench_pass(&b,&moves,cap,temp,1,1);
        for (int block = 0; block < 4; ++block) {
            for (int order = 0; order < 2; ++order) {
                const int arm = (block & 1) ? 1-order : order;
                const long long wall0=bench_ns(CLOCK_MONOTONIC), cpu0=bench_ns(CLOCK_PROCESS_CPUTIME_ID);
                const double sum=bench_pass(&b,&moves,cap,temp,arm,repeats);
                const long long cpu=bench_ns(CLOCK_PROCESS_CPUTIME_ID)-cpu0, wall=bench_ns(CLOCK_MONOTONIC)-wall0;
                printf("{\"type\":\"timing\",\"block\":%d,\"arm\":%d,\"cpu_ns\":%lld,\"wall_ns\":%lld,\"checksum\":%.17g}\n",block,arm,cpu,wall,sum);
            }
        }
    }
    free(b.items); free(b.logw);
    return 0;
}
