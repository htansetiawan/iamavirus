/* Read the shipped inference implementation without modifying it.
 * Including belief.c makes its static count reader available to this probe.
 * No search, policy, scorer or training code is linked. */
#include "belief.c"

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *f = fopen(argv[1], "r"); if (!f) return 3;
    char own[66], received[66];
    if (!fgets(own, sizeof own, f) || !fgets(received, sizeof received, f)) return 4;
    fclose(f); own[strcspn(own, "\r\n")] = 0; received[strcspn(received, "\r\n")] = 0;
    if (strlen(own) != 64 || strlen(received) != 64) return 5;
    fow_init(); zobrist_init();
    Belief b; belief_init_start(&b, WHITE, 200000);
    belief_after_own(&b, MAKE_MOVE(11, 27, NO_PIECE), own); /* recorded d2d4 */
    if (b.count != 1) return 6;
    const double temperature = belief_temperature();
    Position parent = b.items[0]; MoveList moves; generate_moves(&parent, &moves);
    unsigned counts[256]; const unsigned total = history_counts(b.hist[0], &moves, counts);
    float logits[256]; move_logits(&parent, &moves, b.last_own, 1, logits);
    float top = -INFINITY;
    for (int a=0; a<moves.count; ++a) if (logits[a] > top) top = logits[a];
    double z = 0;
    for (int a=0; a<moves.count; ++a) z += exp((double)(logits[a] - top));
    const float log_z = top + (float)log(z);
    printf("{\"kind\":\"parent\",\"history\":\"%016llx\",\"history_total\":%u,\"actions\":%d,\"temperature\":%.17g,\"n0\":%.17g,\"minimum\":%u}\n",
           (unsigned long long)b.hist[0], total, moves.count, temperature, (double)hist_n0, hist_min);
    for (int a=0; a<moves.count; ++a) {
        float features[MM_FEATURES]; move_features(&parent, moves.moves[a], b.last_own, 1, features);
        const float model = expf(logits[a] - log_z);
        const float blend = total >= hist_min ? ((float)counts[a] + hist_n0 * model) / ((float)total + hist_n0) : model;
        Position child = parent; Undo u; make_move(&child, moves.moves[a], &u);
        char view[65], board[65], move[6]; observation(&child, WHITE, view);
        pos_to_board_string(&child, board); move_to_uci(moves.moves[a], move);
        const int survives = !mover_left_king_capturable(&child) && strcmp(view, received) == 0;
        printf("{\"kind\":\"action\",\"move\":\"%s\",\"encoded\":%u,\"board\":\"%s\",\"count\":%u,\"logit\":%.17g,\"model\":%.17g,\"blend\":%.17g,\"survives\":%d,\"features\":[",
               move, (unsigned)moves.moves[a], board, counts[a], (double)logits[a], (double)model, (double)blend, survives);
        for (int k=0; k<MM_FEATURES; ++k) printf("%s%.9g", k ? "," : "", (double)features[k]);
        puts("]}");
    }
    belief_after_opponent(&b, received);
    int indices[32]; double chance[32]; uint64_t rng = 3761111;
    const int distinct = belief_sample(&b, 32, &rng, indices, chance);
    double normalizer=0;
    for (size_t i=0; i<b.count; ++i) normalizer += exp((double)b.logw[i]);
    for (size_t i=0; i<b.count; ++i) {
        char board[65]; pos_to_board_string(&b.items[i], board);
        printf("{\"kind\":\"retained\",\"index\":%zu,\"board\":\"%s\",\"logw\":%.17g,\"weight\":%.17g}\n",
               i, board, (double)b.logw[i], exp((double)b.logw[i])/normalizer);
    }
    for (int i=0; i<distinct; ++i)
        printf("{\"kind\":\"sample\",\"index\":%d,\"weight\":%.17g}\n", indices[i], chance[i]);
    unsigned long lookups,hits;belief_history_stats(&lookups,&hits);
    printf("{\"kind\":\"summary\",\"worlds\":%zu,\"distinct\":%d,\"lookups\":%lu,\"hits\":%lu,\"capped\":%d}\n",
           b.count, distinct, lookups, hits, b.overflowed);
    belief_free(&b); return 0;
}
