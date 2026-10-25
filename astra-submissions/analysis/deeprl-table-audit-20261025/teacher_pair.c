#define _POSIX_C_SOURCE 199309L
#include "teacher_pair.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec + t.tv_nsec*1e-9;
}

int astra_teacher_pair(const Belief *b, const GtcfrParams *params, SearchResult *out) {
    const char *value=getenv("ASTRA_TEACHER_B");
    double budget=value ? atof(value) : 0;
    if (!isfinite(budget) || budget<=0) return gtcfr_decide(b,params,out);
    int strong_first=getenv("ASTRA_TEACHER_STRONG_FIRST") &&
                     atoi(getenv("ASTRA_TEACHER_STRONG_FIRST"));
    int ok=0;
    for (int i=0; i<2; ++i) {
        int strong=strong_first ? i==0 : i==1;
        GtcfrParams p=*params;
        p.seconds=budget*(strong ? 4:1);
        SearchResult teacher;
        double start=now();
        int result=gtcfr_decide(b,&p,strong ? &teacher:out);
        fprintf(stderr,"astra: paired_search budget=%.9g elapsed=%.9g ok=%d\n",
                p.seconds,now()-start,result);
        if (!strong) ok=result;
    }
    return ok;
}
