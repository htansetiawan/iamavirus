/* Offline bridge to the exact v37 model/history implementation. No edits to
 * its sources. Full boards supply the existing model's hypothetical parent;
 * the response student has a separate view-only API. */
#include "belief.c"

static Position current;
static uint64_t histories[2];
static Move previous;

int prior_load(const char *path) {
    fow_init();
    read_history_table(path);
    return hist_n > 0;
}

void prior_start(void) {
    char view[65];
    pos_start(&current); previous = 0;
    for (int s = 0; s < 2; ++s) {
        observation(&current, s, view);
        histories[s] = history_mix(0, view_hash(view));
    }
}

int prior_state(char board[65], char white[65], char black[65]) {
    pos_to_board_string(&current, board);
    observation(&current, WHITE, white); observation(&current, BLACK, black);
    return current.side;
}

uint64_t prior_history(int side) { return histories[side]; }

int prior_scores(int full, uint16_t moves[256], double probabilities[256],
                 unsigned counts[256], unsigned *total) {
    MoveList list; generate_moves(&current, &list);
    if (!list.count) return 0;
    float logits[256], top = -INFINITY;
    move_logits(&current, &list, previous, full, logits);
    for (int j = 0; j < list.count; ++j) if (logits[j] > top) top = logits[j];
    double z = 0;
    for (int j = 0; j < list.count; ++j) z += exp((double)(logits[j] - top));
    const float log_z = top + (float)log(z);
    *total = history_counts(histories[current.side], &list, counts);
    for (int j = 0; j < list.count; ++j) {
        moves[j] = list.moves[j];
        probabilities[j] = expf(logits[j] - log_z);
    }
    return list.count;
}

int prior_step(uint16_t move) {
    MoveList list; generate_moves(&current, &list);
    int valid = 0;
    for (int j = 0; j < list.count; ++j) if (list.moves[j] == move) valid = 1;
    if (!valid) return -1;
    const int mover = current.side;
    Undo undo; make_move(&current, move, &undo); previous = move;
    char view[65];
    for (int s = 0; s < 2; ++s) {
        observation(&current, s, view);
        histories[s] = history_mix(s == mover ? history_mix(histories[s], move) : histories[s], view_hash(view));
    }
    return mover_left_king_capturable(&current);
}
