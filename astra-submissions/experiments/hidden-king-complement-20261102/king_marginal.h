/* Observation-only, read-only marginal. Never receives a true board. */
static void astra_king_marginal(const Belief *b, int side, int decision,
                                double temperature) {
    double sharp[64] = {0}, flat[64] = {0}, total = 0, total_flat = 0;
    size_t missing = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const Position *p = &b->items[i];
        int square = -1;
        for (int s = 0; s < 64; ++s)
            if (p->piece[s] == KING && p->color[s] == (side ^ 1)) square = s;
        const double lw = b->logw ? b->logw[i] : 0.0;
        const double w = exp(lw), wf = exp(lw / temperature);
        total += w; total_flat += wf;
        if (square >= 0) { sharp[square] += w; flat[square] += wf; }
        else ++missing;
    }
    fprintf(stderr, "astra-king-location %d %zu %zu", decision, b->count, missing);
    for (int s = 0; s < 64; ++s)
        fprintf(stderr, " %.17g", total > 0 ? sharp[s] / total : 0);
    for (int s = 0; s < 64; ++s)
        fprintf(stderr, " %.17g", total_flat > 0 ? flat[s] / total_flat : 0);
    fprintf(stderr, "\n");
}
