/* Offline features of each hypothetical true parent; same inputs the belief
 * model has per world. Never an actor-observation-only policy. */
#include "../deployed-prior-comparison-20261102/prior.c"

int interaction_features(uint16_t moves[256], float x[256 * 26],
                         float full[256], float cheap[256], unsigned counts[256],
                         unsigned *total, uint8_t surprise[256]) {
    MoveList l; generate_moves(&current, &l);
    char victim_view[65]; observation(&current, current.side ^ 1, victim_view);
    move_logits(&current, &l, previous, 1, full);
    move_logits(&current, &l, previous, 0, cheap);
    *total = history_counts(histories[current.side], &l, counts);
    for (int j = 0; j < l.count; ++j) {
        float all[MM_FEATURES]; move_features(&current, l.moves[j], previous, 1, all);
        moves[j] = l.moves[j]; memcpy(x + 26 * j, all, 26 * sizeof(float));
        surprise[j] = all[MM_CAPTURE] > 0 && victim_view[MOVE_FROM(l.moves[j])] == '?';
    }
    return l.count;
}

/* Exportable sparse quadratic table. W is row-major, upper triangle plus
 * selected continuous-feature diagonals. Zero residual preserves base logits. */
void interaction_logits(const float *x, const float *base, int n, int features,
                        const float *linear, const float *quadratic, float *out) {
    for (int r = 0; r < n; ++r) {
        const float *v = x + 26 * r;
        int active[26], count = 0; float delta = 0;
        for (int i = 0; i < features; ++i) {
            if (v[i] != 0) { active[count++] = i; delta += linear[i] * v[i]; }
        }
        for (int a = 0; a < count; ++a) {
            const int i = active[a];
            for (int b = a; b < count; ++b) {
                const int j = active[b];
                delta += quadratic[features * i + j] * v[i] * v[j];
            }
        }
        out[r] = base[r] + delta;
    }
}
