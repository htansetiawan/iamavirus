#include "mixture.c"

static Move parse_uci(const char *text) {
    if (!text || (strlen(text) != 4 && strlen(text) != 5)) abort();
    for (int i = 0; i < 4; ++i) if ((i % 2 == 0 && (text[i] < 'a' || text[i] > 'h')) || (i % 2 && (text[i] < '1' || text[i] > '8'))) abort();
    int promo = NO_PIECE;
    if (text[4]) { const char *s = strchr("nbrq", text[4]); if (!s) abort(); promo = (int)(s - "nbrq") + KNIGHT; }
    return MAKE_MOVE((text[1] - '1') * 8 + text[0] - 'a', (text[3] - '1') * 8 + text[2] - 'a', promo);
}

void *tb_create(int us, size_t cap, uint64_t seed) {
    fow_init(); zobrist_init(); Mixture *b = checked_alloc(1, sizeof(*b));
    const char *mode = getenv("ASTRA_TEMPORAL_MODEL"), *temp = getenv("MIST_MODEL_TEMP");
    mix_init(b, us, cap, seed, mode ? atoi(mode) : 0, temp ? (float)atof(temp) : 2);
    if ((b->temporal != 0 && b->temporal != 1) || !isfinite(b->temperature) || b->temperature <= 0 || !cap) abort();
    return b;
}
void tb_free(void *handle) { mix_free(handle); free(handle); }
size_t tb_step(void *handle, const char *own_move, const char *view) {
    Mixture *b = handle; if (!b->count) return 0;
    return own_move && own_move[0] ? mix_own(b, parse_uci(own_move), view) : mix_opponent(b, view);
}
static uint64_t cm_checksum_mix(uint64_t s, uint64_t v) {
    uint64_t z = s ^ (v + 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL; z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}
uint64_t tb_checksum(const void *handle) {
    const Mixture *b = handle; uint64_t h = cm_checksum_mix(b->rng, b->cap);
    h = cm_checksum_mix(h, ((uint64_t)b->last_own << 32) | (unsigned)b->us);
    h = cm_checksum_mix(h, (unsigned)b->overflowed);
    for (size_t i = 0; i < b->count; ++i) {
        h = cm_checksum_mix(h, position_key(&b->boards[i].position));
        for (size_t j = b->boards[i].begin; j < b->boards[i].end; ++j) {
            uint32_t bits; memcpy(&bits, &b->contexts[j].logw, sizeof(bits));
            h = cm_checksum_mix(h, ((uint64_t)bits << 32) | b->contexts[j].recent);
        }
    }
    return cm_checksum_mix(h, b->count);
}
void tb_probe(const void *handle, const char *truth, int side, uint64_t castle, int ep, uint32_t context, double out[10]) {
    const Mixture *b = handle; memset(out, 0, 10 * sizeof(double)); out[0] = out[1] = b->count; out[7] = b->overflowed;
    uint64_t target = 0; Position t;
    if (truth && pos_from_board_string(&t, truth, side, castle, ep) == 0) target = position_key(&t);
    double total = 0, square = 0, weighted_log = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *w = &b->boards[i]; double board_mass = 0; int match = position_key(&w->position) == target;
        if (match) out[8] += 1;
        for (size_t j = w->begin; j < w->end; ++j) {
            const MixContext *c = &b->contexts[j]; double mass = exp((double)c->logw);
            board_mass += mass; square += mass * mass;
            if (c->recent & (1U << 23)) out[4] += mass;
            if (match) { out[2] += mass; if (c->recent == context) { out[3] += mass; out[9] += 1; } }
        }
        total += board_mass; if (board_mass > 0) weighted_log += board_mass * log(board_mass);
    }
    if (total > 0) { out[2] /= total; out[3] /= total; out[4] /= total; out[5] = log(total) - weighted_log / total; out[6] = total * total / square; }
}
double tb_king_risk(const void *handle, const char *own_move) {
    const Mixture *b = handle; Move move = parse_uci(own_move); double total = 0, losses = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *w = &b->boards[i]; Position p = w->position; double mass = exp((double)w->logw);
        MoveList legal; generate_moves(&p, &legal); int found = 0;
        for (int j = 0; j < legal.count; ++j) if (legal.moves[j] == move) found = 1;
        total += mass; if (!found) { losses += mass; continue; }
        Undo u; make_move(&p, move, &u);
        if (king_square(&p, b->us ^ 1) >= 0 && mover_left_king_capturable(&p)) losses += mass;
    }
    return total > 0 ? losses / total : NAN;
}
void tb_stats(const void *handle, double out[5]) {
    const Mixture *b = handle; size_t largest = 0;
    for (size_t i = 0; i < b->count; ++i) if (b->boards[i].end - b->boards[i].begin > largest) largest = b->boards[i].end - b->boards[i].begin;
    out[0] = b->context_count; out[1] = b->count * sizeof(MixBoard) + b->context_count * sizeof(MixContext);
    out[2] = b->peak_candidates; out[3] = largest; out[4] = sizeof(MixBoard);
}
