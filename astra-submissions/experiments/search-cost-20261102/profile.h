#ifndef ASTRA_SEARCH_PROFILE_H
#define ASTRA_SEARCH_PROFILE_H
enum { PROF_OTHER, PROF_SOLVE, PROF_STRATEGY, PROF_GROW, PROF_SELECT, PROF_EXPAND, PROF_SF, PROF_N };
void prof_begin(void);
int prof_enter(int kind);
void prof_leave(int token);
void prof_report(int nodes, int iterations, double budget, int async);
#endif
