/* Inserted only in the offline audit copy, after Candidate is declared.
 * Observers read immutable candidates and do not consume RNG or change weights. */
static const char *astra_truth_board;
void astra_stage_truth(const char *board) { astra_truth_board = board; }

static void astra_stage_candidates(const Belief *b, const Candidate *candidates,
                                  size_t count, const uint32_t *chosen, size_t keep,
                                  const char *phase) {
    if (!astra_truth_board) return;
    double top = -INFINITY;
    for (size_t k = 0; k < keep; ++k) {
        const size_t i = chosen ? chosen[k] : k;
        assert(i < count);
        if (candidates[i].logw > top) top = candidates[i].logw;
    }
    double mass = 0, total = 0; size_t matches = 0;
    for (size_t k = 0; k < keep; ++k) {
        const size_t i = chosen ? chosen[k] : k;
        const Candidate *c = &candidates[i];
        const double weight = exp((double)c->logw - top);
        total += weight;
        Position p = b->items[c->parent]; Undo undo;
        make_move(&p, c->move, &undo);
        char board[65]; pos_to_board_string(&p, board);
        if (strcmp(board, astra_truth_board) == 0) {
            ++matches; mass += weight;
            char move[6]; move_to_uci(c->move, move);
            printf("{\"phase\":\"%s_match\",\"key\":\"%llx\",\"parent\":%u,\"move\":\"%s\",\"logw\":%.17g}\n",
                phase, (unsigned long long)c->key, c->parent, move, (double)c->logw);
        }
    }
    printf("{\"phase\":\"%s\",\"count\":%zu,\"truth_placements\":%zu,\"truth_mass\":%.17g}\n",
        phase, keep, matches, total > 0 ? mass / total : 0);
}
