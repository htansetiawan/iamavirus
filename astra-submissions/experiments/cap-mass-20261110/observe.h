/* Diagnostic only. Include after the native Ranked typedef. No RNG, ranking,
 * position, history or log-weight is changed. Observe the FIRST event of each
 * kind in this process, exporting raw weights and keys for independent review. */
#ifndef ASTRA_CAP_MASS_OBSERVE_H
#define ASTRA_CAP_MASS_OBSERVE_H
#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "correction.h"

static void astra_cap_observe(int stage, size_t n, size_t keep, const Ranked *r,
                              const void *weights, size_t stride, size_t offset) {
    static int seen[2];
    const char *dir=getenv("ASTRA_CAP_DUMP_DIR");
    if (!dir || !*dir || stage<0 || stage>1 || seen[stage]) return;
    seen[stage]=1;
    if (!keep || keep>=n || n>UINT32_MAX || 32+12*n+4*keep > 64*1024*1024) {
        fprintf(stderr,"astra-cap-mass: invalid or oversized snapshot\n");exit(9);
    }
    struct timespec start,end;clock_gettime(CLOCK_MONOTONIC,&start);
    float *lw=malloc(n*sizeof(float)); double *keys=malloc(n*sizeof(double));
    uint32_t *selected=malloc(keep*sizeof(uint32_t));
    if (!lw || !keys || !selected) exit(10);
    double top=-INFINITY,cutoff=INFINITY;
    for (size_t i=0;i<n;++i) {
        if (weights) memcpy(&lw[i],(const char *)weights+i*stride+offset,sizeof(float)); else lw[i]=0;
        if (!isfinite(lw[i]) || r[i].index>=n || !isfinite(r[i].key)) exit(11);
        if (lw[i]>top) top=lw[i];
        keys[r[i].index]=r[i].key;
        if (i>=keep && r[i].key<cutoff) cutoff=r[i].key;
    }
    long double total=0,retained=0,adjusted=0,squared=0;
    for (size_t i=0;i<n;++i) {const double w=exp((double)lw[i]-top);total+=w;squared+=(long double)w*w;}
    for (size_t j=0;j<keep;++j) {
        selected[j]=r[j].index;
        retained+=exp((double)lw[selected[j]]-top);
        adjusted+=exp(cap_corrected_logweight(lw[selected[j]],cutoff)-top);
    }
    char path[4096];const char *label=stage?"paid":"opponent";
    if (snprintf(path,sizeof path,"%s/%s.bin",dir,label)>=(int)sizeof path) exit(12);
    FILE *f=fopen(path,"wx");if (!f) exit(13);
    const uint64_t dimensions[2]={n,keep};const double scalars[2]={cutoff,top};
    int ok=fwrite(dimensions,sizeof(uint64_t),2,f)==2 && fwrite(scalars,sizeof(double),2,f)==2
        && fwrite(lw,sizeof(float),n,f)==n && fwrite(keys,sizeof(double),n,f)==n
        && fwrite(selected,sizeof(uint32_t),keep,f)==keep;
    if (fclose(f) || !ok) exit(14);
    clock_gettime(CLOCK_MONOTONIC,&end);
    const double elapsed=(double)(end.tv_sec-start.tv_sec)+1e-9*(end.tv_nsec-start.tv_nsec);
    fprintf(stderr,"astra-cap-mass: {\"stage\":\"%s\",\"n\":%zu,\"keep\":%zu,"
          "\"cutoff\":%.17g,\"max_logw\":%.17g,\"scaled_total\":%.17g,\"scaled_retained\":%.17g,"
          "\"discarded_fraction\":%.17g,\"corrected_fraction\":%.17g,\"effective_size\":%.17g,"
          "\"observer_seconds\":%.9g,\"bytes\":%zu}\n",label,n,keep,cutoff,top,(double)total,(double)retained,
          (double)(1-retained/total),(double)(adjusted/total),(double)(total*total/squared),elapsed,32+12*n+4*keep);
    free(lw);free(keys);free(selected);
}
#endif
