/* Appended to the isolated v38 movemodel.c to reuse theta_full and features. */
#include <math.h>
#include "weights.h"

enum { COMPACT_RANK = 16, COMPACT_FEATURES = 26 };

static float dot16(const float *a, const float *b) {
    float total = 0.0f;
    for (int i = 0; i < COMPACT_RANK; ++i) total += a[i] * b[i];
    return total;
}

static bb_t mover_view(const Position *p, const MoveList *moves) {
    bb_t seen = p->by_color[p->side];
    for (int j = 0; j < moves->count; ++j) {
        Move move = moves->moves[j];
        int to = MOVE_TO(move);
        seen |= UINT64_C(1) << to;
        if (to == p->ep && p->piece[to] == NO_PIECE && p->piece[MOVE_FROM(move)] == PAWN)
            seen |= UINT64_C(1) << (to + (p->side == WHITE ? -8 : 8));
    }
    return seen;
}

static int piece_code(const Position *p, int square) {
    if (p->piece[square] == NO_PIECE) return 0;
    return 1 + p->piece[square] + 6 * (p->color[square] != p->side);
}

static int castle_feature(const Position *p, int square) {
    if (!(p->castle_rooks & (UINT64_C(1) << square))) return 0;
    int color = square < 8 ? WHITE : BLACK;
    int home = color == WHITE ? 0 : 56;
    return (square == home || square == home + 7) && p->piece[square] == ROOK &&
           p->color[square] == color && p->piece[home + 4] == KING && p->color[home + 4] == color;
}

static void compact_context(const Position *p, const MoveList *moves, float out[COMPACT_RANK]) {
    const int flip = p->side == WHITE ? 0 : 56;
    const bb_t own = mover_view(p, moves), other = visible_squares(p, p->side ^ 1);
    float piece_sum[COMPACT_RANK] = {0}, view_sum[COMPACT_RANK] = {0}, castle_sum[COMPACT_RANK] = {0};
    for (int relative = 0; relative < 64; ++relative) {
        int sq = relative ^ flip;
        int mask = ((own >> sq) & 1) | (((other >> sq) & 1) << 1);
        const float *piece = compact_piece[13 * relative + piece_code(p, sq)];
        const float *view = compact_visibility[4 * relative + mask];
        for (int i = 0; i < COMPACT_RANK; ++i) {
            piece_sum[i] += piece[i];
            view_sum[i] += view[i];
        }
        if (castle_feature(p, sq))
            for (int i = 0; i < COMPACT_RANK; ++i) castle_sum[i] += compact_castling[relative][i];
    }
    const float *ep = compact_en_passant[p->ep < 0 ? 0 : (p->ep ^ flip) + 1];
    float halfmove = (float)(p->halfmove < 0 ? 0 : p->halfmove > 100 ? 100 : p->halfmove) * 0.01f;
    for (int i = 0; i < COMPACT_RANK; ++i) {
        float v = piece_sum[i] + view_sum[i] + castle_sum[i] + ep[i] +
                  (halfmove * compact_halfmove[i] + compact_halfmove_bias[i]);
        out[i] = fminf(1.0f, fmaxf(-1.0f, v));
    }
}

void compact_full_logp(const Position *p, const MoveList *moves, Move previous,
                       int learned, float *out, float *residual) {
    float context[COMPACT_RANK], coefficients[COMPACT_FEATURES], promotion[5];
    float base[256], delta[256], source[64], target[64];
    unsigned char quiet[256];
    bb_t source_ready = 0, target_ready = 0;
    const int flip = p->side == WHITE ? 0 : 56;
    float top = -INFINITY;
    double new_top = -INFINITY;
    int quiet_count = 0, changed = 0;
    if (learned) {
        compact_context(p, moves, context);
        for (int k = 0; k < COMPACT_FEATURES; ++k)
            coefficients[k] = dot16(context, compact_feature[k]) + compact_scalar[k];
        for (int k = 0; k < 5; ++k) promotion[k] = dot16(context, compact_promotion[k]);
    }
    for (int j = 0; j < moves->count; ++j) {
        Move move = moves->moves[j];
        float x[MM_FEATURES];
        move_features(p, move, previous, 1, x);
        float logit = 0.0f;
        for (int k = 0; k < MM_FEATURES; ++k) logit += theta_full[k] * x[k];
        base[j] = logit;
        if (logit > top) top = logit;
        quiet[j] = x[MM_CAPTURE] == 0.0f;
        float change = 0.0f;
        if (learned && quiet[j]) {
            int from = MOVE_FROM(move), to = MOVE_TO(move), promo = MOVE_PROMO(move);
            bb_t from_bit = UINT64_C(1) << from, to_bit = UINT64_C(1) << to;
            if (!(source_ready & from_bit)) {
                source[from] = dot16(context, compact_source[13 * (from ^ flip) + piece_code(p, from)]);
                source_ready |= from_bit;
            }
            if (!(target_ready & to_bit)) {
                target[to] = dot16(context, compact_target[13 * (to ^ flip) + piece_code(p, to)]);
                target_ready |= to_bit;
            }
            change = source[from] + target[to] + promotion[promo == NO_PIECE ? 0 : 5 - promo];
            for (int k = 0; k < COMPACT_FEATURES; ++k) change += coefficients[k] * x[k];
            double new_logit = (double)logit + change;
            if (new_logit > new_top) new_top = new_logit;
            ++quiet_count;
            changed |= change != 0.0f;
        }
        delta[j] = change;
        if (residual) residual[j] = change;
    }
    double sum = 0.0, old_quiet = 0.0;
    for (int j = 0; j < moves->count; ++j) {
        double mass = exp((double)(base[j] - top));
        sum += mass;
        if (quiet[j]) old_quiet += mass;
    }
    const float log_z = top + (float)log(sum);
    for (int j = 0; j < moves->count; ++j) out[j] = base[j] - log_z;
    if (quiet_count <= 1 || !changed) return;
    double new_quiet = 0.0;
    for (int j = 0; j < moves->count; ++j)
        if (quiet[j]) new_quiet += exp((double)base[j] + delta[j] - new_top);
    double offset = (double)top + log(old_quiet) - new_top - log(new_quiet);
    for (int j = 0; j < moves->count; ++j)
        if (quiet[j]) out[j] = (float)((double)base[j] + delta[j] + offset - log_z);
}
