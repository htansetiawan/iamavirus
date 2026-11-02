#define _POSIX_C_SOURCE 200809L
#include "profile.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

typedef struct { int kind; double wall, cpu, child_wall, child_cpu; } Frame;
static Frame stack[128];
static int depth, active;
static double wall[PROF_N], cpu[PROF_N], total_wall, total_cpu;
static unsigned long count[PROF_N];
#ifdef PROFILE_TEST_CLOCK
static double tick;
static double wall_now(void) { return ++tick; }
static double cpu_now(void) { return tick * .5; }
#else
static double clock_value(clockid_t id) {
    struct timespec t; assert(clock_gettime(id, &t) == 0);
    return t.tv_sec + t.tv_nsec * 1e-9;
}
static double wall_now(void) { return clock_value(CLOCK_MONOTONIC); }
static double cpu_now(void) { return clock_value(CLOCK_THREAD_CPUTIME_ID); }
#endif

void prof_begin(void) {
    assert(depth == 0);
    memset(wall, 0, sizeof wall); memset(cpu, 0, sizeof cpu); memset(count, 0, sizeof count);
    total_wall = total_cpu = 0; active = 1;
}
int prof_enter(int kind) {
    if (!active) return -1;
    assert(kind >= 0 && kind < PROF_N && depth < 128);
    int token = depth++;
    stack[token] = (Frame){kind, wall_now(), cpu_now(), 0, 0};
    return token;
}
void prof_leave(int token) {
    if (token < 0) return;
    const double wend = wall_now(), cend = cpu_now();
    assert(token == --depth);
    const Frame f = stack[token];
    const double w = wend - f.wall, c = cend - f.cpu;
    wall[f.kind] += w - f.child_wall; cpu[f.kind] += c - f.child_cpu; ++count[f.kind];
    if (depth) { stack[depth-1].child_wall += w; stack[depth-1].child_cpu += c; }
    else { total_wall = w; total_cpu = c; }
}
void prof_report(int nodes, int iterations, double budget, int async) {
    static const char *names[] = {"other", "solver", "strategy", "growth", "selection", "expansion", "stockfish"};
    assert(depth == 0); active = 0;
    fprintf(stderr, "astra-search-cost {\"wall\":%.9f,\"cpu\":%.9f,\"nodes\":%d,\"iterations\":%d,\"budget\":%.9f,\"async\":%d,\"buckets\":{",
            total_wall,total_cpu,nodes,iterations,budget,async);
    for (int i=0;i<PROF_N;++i)
        fprintf(stderr,"%s\"%s\":{\"wall\":%.9f,\"cpu\":%.9f,\"calls\":%lu}",i?",":"",names[i],wall[i],cpu[i],count[i]);
    fprintf(stderr,"}}\n");
}
