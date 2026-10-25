#include "teacher_dump.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int astra_teacher_dump(const Game *g, const double *x, int root_I,
                       const MoveList *moves, const SearchResult *result,
                       const Belief *belief, const int *indices,
                       const double *shares, int sampled,
                       const GtcfrParams *params) {
    const char *path = getenv("MIST_TEACHER_OUT");
    if (!path || !*path) return 0;
    TeacherTargets t = teacher_targets(g,x);
    int o = g->is_offset[root_I];
    double mass = t.cf_mass[root_I], v = 0;
    for (int a=0; a<moves->count; ++a) v += x[o+a]*t.cf_q[o+a];
    int zero_mass = 0;
    for (int I=0; I<g->n_infosets; ++I) zero_mass += t.cf_mass[I] == 0;
    FILE *f = fopen(path,"a");
    if (!f) { teacher_targets_free(&t); return -1; }
    char selected[6]; move_to_uci(result->move, selected);
    fprintf(f,"{\"schema\":1,\"stage\":\"solver_before_frontend_fallback\","
              "\"solver_move\":\"%s\",\"root_infoset\":%d,\"root_value\":%.17g,\"solver_value\":%.17g,"
              "\"cf_mass\":%.17g,\"own_reach\":%.17g,\"root_histories\":%d,"
              "\"own_reach_consistent\":%s,\"zero_mass_infosets\":%d,"
              "\"nodes\":%d,\"infosets\":%d,\"slots\":%d,\"iterations\":%d,"
              "\"search_budget_seconds\":%.17g,\"root_loss_value\":%.17g,"
              "\"belief_count\":%zu,\"belief_overflowed\":%s,\"samples\":[",
            selected,root_I,t.root_value,result->value,mass,t.own_reach[root_I],t.histories[root_I],
            t.recall_ok ? "true":"false",zero_mass,g->n_nodes,g->n_infosets,
            g->n_slots,result->iterations,params->seconds,
            params->king_risk > 1 ? -params->king_risk : -1,
            belief->count,belief->overflowed ? "true":"false");
    for (int k=0; k<sampled; ++k) {
        /* Sampled hypotheses are diagnostic OUTPUT, never actor input.
           No replay truth is passed into this exporter or the engine. */
        char board[65]; pos_to_board_string(&belief->items[indices[k]],board);
        fprintf(f,"%s{\"belief_index\":%d,\"weight\":%.17g,\"hypothesis_board\":\"%s\"}",
                k ? ",":"",indices[k],shares[k],board);
    }
    fprintf(f,"],\"avoid_moves\":[");
    for (int a=0; a<params->avoid_count; ++a) {
        char uci[6]; move_to_uci(params->avoid[a],uci);
        fprintf(f,"%s\"%s\"",a ? ",":"",uci);
    }
    fprintf(f,"],\"actions\":[");
    for (int a=0; a<moves->count; ++a) {
        char uci[6]; move_to_uci(moves->moves[a],uci);
        fprintf(f,"%s{\"uci\":\"%s\",\"probability\":%.17g,\"cf_q\":%.17g,",
                a ? ",":"",uci,x[o+a],t.cf_q[o+a]);
        if (mass > 0)
            fprintf(f,"\"q\":%.17g,\"advantage\":%.17g}",
                    t.cf_q[o+a]/mass,(t.cf_q[o+a]-v)/mass);
        else fprintf(f,"\"q\":null,\"advantage\":null}");
    }
    fprintf(f,"]}\n");
    int failed = ferror(f);
    failed |= fclose(f) != 0;
    teacher_targets_free(&t);
    return failed ? -1:1;
}
