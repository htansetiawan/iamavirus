/* Observability only: original paired search completes before any census. */
#include "gtcfr.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int astra_guard_pair_original(const Belief *, const GtcfrParams *, SearchResult *, const Move *, int);

static int contains(const Move *moves, int n, Move move) {
    for (int i = 0; i < n; ++i) if (moves[i] == move) return 1;
    return 0;
}

int astra_guard_pair(const Belief *b, const GtcfrParams *params, SearchResult *out,
                     const Move *alternative, int alternative_count) {
    const int ok = astra_guard_pair_original(b, params, out, alternative, alternative_count);
    const char *path = getenv("ASTRA_POPULATION_OUT");
    if (!path || !ok) return ok;
    const int draws = params->samples > 0 ? params->samples : 1;
    int *idx = malloc((size_t)draws * sizeof(int));
    double *share = malloc((size_t)draws * sizeof(double));
    uint64_t rng = params->seed ^ UINT64_C(0x5eed);
    const int k = belief_sample(b, draws, &rng, idx, share);
    if (!k) exit(5);
    MoveList moves;
    generate_moves(&b->items[idx[0]], &moves);
    if (moves.count > 64) exit(6); /* This diagnostic's signature width. */
    FILE *f = fopen(path, "wx");
    if (!f) exit(7);
    const double temp = belief_temperature();
    const size_t stride = b->count > 20000 ? (b->count+19999)/20000 : 1;
    double denom[3] = {0}, guard_denom[2] = {0};
    double fatal[64][3] = {{0}}, guard_fatal[64][2] = {{0}};
    double sampled_fatal[64] = {0};
    size_t illegal[64] = {0};
    fprintf(f, "{\"count\":%zu,\"us\":%d,\"temperature\":%.9g,\"guard_stride\":%zu,\"moves\":[",
            b->count, b->us, temp, stride);
    for (int a = 0; a < moves.count; ++a) {
        char uci[6]; move_to_uci(moves.moves[a], uci);
        fprintf(f, "%s{\"uci\":\"%s\",\"base_kept\":%s,\"candidate_kept\":%s}", a ? "," : "", uci,
                contains(params->avoid, params->avoid_count, moves.moves[a]) ? "false" : "true",
                contains(alternative, alternative_count, moves.moves[a]) ? "false" : "true");
    }
    fputs("],\"samples\":[", f);
    for (int j = 0; j < k; ++j)
        fprintf(f, "%s{\"index\":%d,\"weight\":%.17g}", j ? "," : "", idx[j], share[j]);
    fputs("],\"worlds\":[", f);
    for (size_t i = 0; i < b->count; ++i) {
        const double lw = b->logw ? b->logw[i] : 0;
        const double w[3] = {exp(lw/temp), exp(lw), 1};
        for (int c = 0; c < 3; ++c) denom[c] += w[c];
        if (i % stride == 0) for (int c = 0; c < 2; ++c) guard_denom[c] += w[c];
        Position p = b->items[i];
        MoveList legal; generate_moves(&p, &legal);
        uint64_t legal_mask = 0, fatal_mask = 0;
        for (int a = 0; a < moves.count; ++a) {
            if (!contains(legal.moves, legal.count, moves.moves[a])) { ++illegal[a]; continue; }
            legal_mask |= UINT64_C(1) << a;
            Undo u; make_move(&p, moves.moves[a], &u);
            const int loss = mover_left_king_capturable(&p);
            unmake_move(&p, moves.moves[a], &u);
            if (!loss) continue;
            fatal_mask |= UINT64_C(1) << a;
            for (int c = 0; c < 3; ++c) fatal[a][c] += w[c];
            if (i % stride == 0) for (int c = 0; c < 2; ++c) guard_fatal[a][c] += w[c];
            for (int j = 0; j < k; ++j) if ((size_t)idx[j] == i) sampled_fatal[a] += share[j];
        }
        char board[65]; pos_to_board_string(&p, board);
        fprintf(f, "%s{\"index\":%zu,\"board\":\"%s\",\"logw\":%.9g,\"side\":%d,"
                "\"castle\":\"%016" PRIx64 "\",\"ep\":%d,\"halfmove\":%d,\"hist\":\"%016" PRIx64 "\","
                "\"legal\":\"%016" PRIx64 "\",\"fatal\":\"%016" PRIx64 "\"}",
                i ? "," : "", i, board, lw, p.side, p.castle_rooks, p.ep, p.halfmove,
                b->hist ? b->hist[i] : 0, legal_mask, fatal_mask);
    }
    fputs("],\"risks\":[", f);
    for (int a = 0; a < moves.count; ++a) {
        fprintf(f, "%s{\"fitted\":%.17g,\"sharpened\":%.17g,\"uniform\":%.17g,"
                "\"guard_fitted\":%.17g,\"guard_sharpened\":%.17g,\"sampled\":%.17g,\"illegal_worlds\":%zu}",
                a ? "," : "", fatal[a][0]/denom[0], fatal[a][1]/denom[1], fatal[a][2]/denom[2],
                guard_fatal[a][0]/guard_denom[0], guard_fatal[a][1]/guard_denom[1], sampled_fatal[a], illegal[a]);
    }
    fputs("]}\n", f);
    if (fclose(f)) exit(8);
    free(idx); free(share);
    return ok;
}
