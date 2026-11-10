/* Reuse the exact frozen rank RNG, comparators, partition and shrink body.
 * Only the standalone audit wrapper produces corrected masses. The native
 * belief updater and its public symbols remain unmodified. */
#include "belief.c"
#include "correction.h"

double astra_cap_corrected(double logw, double cutoff) { return cap_corrected_logweight(logw,cutoff); }
void astra_cap_uniforms(uint64_t *seed, size_t n, double *out) {
    for (size_t i=0;i<n;++i) out[i]=unit_open(seed);
}

int astra_cap_draw(const float *logw, size_t n, size_t keep, uint64_t *rng, int partition,
                   uint32_t *indices, double *corrected, double *cutoff) {
    if (!n || !keep || n > UINT32_MAX) return 0;
    if (keep >= n) {
        *cutoff = INFINITY;
        for (size_t i=0; i<n; ++i) { indices[i]=(uint32_t)i; corrected[i]=logw[i]; }
        return (int)n;
    }
    Ranked *r = malloc(n*sizeof(*r));
    if (!r) return 0;
    for (size_t i=0; i<n; ++i) {
        r[i].key=log(-log(unit_open(rng)))-(double)logw[i]; r[i].index=(uint32_t)i;
    }
    double threshold;
    if (partition) {
        select_smallest(r,n,keep);
        threshold=INFINITY;
        for (size_t i=keep; i<n; ++i) if (r[i].key<threshold) threshold=r[i].key;
    } else { qsort(r,n,sizeof(*r),by_rank); threshold=r[keep].key; }
    for (size_t i=0; i<keep; ++i) indices[i]=r[i].index;
    free(r);
    qsort(indices,keep,sizeof(*indices),by_index_u32);
    for (size_t i=0; i<keep; ++i) corrected[i]=cap_corrected_logweight(logw[indices[i]],threshold);
    *cutoff=threshold;
    return (int)keep;
}

int astra_native_shrink_verify(const float *logw, size_t n, size_t keep, uint64_t seed) {
    if (!n || !keep || keep>=n) return 0;
    Belief b={0}; b.count=n; b.rng=seed;
    b.items=calloc(n,sizeof(Position)); b.hist=malloc(n*sizeof(uint64_t)); b.logw=malloc(n*sizeof(float));
    uint32_t *indices=malloc(keep*sizeof(uint32_t)); double *corrected=malloc(keep*sizeof(double));
    if (!b.items || !b.hist || !b.logw || !indices || !corrected) abort();
    for (size_t i=0;i<n;++i) { b.hist[i]=i+1; b.logw[i]=logw[i]; b.items[i].halfmove=(int)i; }
    uint64_t rng=seed; double cutoff;
    const int k=astra_cap_draw(logw,n,keep,&rng,0,indices,corrected,&cutoff);
    belief_shrink(&b,keep);
    int ok=k==(int)keep && rng==b.rng && b.count==keep && b.overflowed;
    for (size_t i=0;i<keep;++i)
        if (b.hist[i] != indices[i]+1 || b.items[i].halfmove != (int)indices[i] || b.logw[i] != logw[indices[i]]) ok=0;
    belief_free(&b); free(indices); free(corrected);
    return ok;
}

/* Four coupled estimators per subset: old raw mass, corrected raw mass,
 * old normalized mass, corrected normalized mass. The last two are ratios.
 * Return sums/squares plus paired ratio differences; labels are arbitrary
 * fixed subsets, never a true-board flag that can enter a playing engine. */
int astra_cap_batch(const float *logw, const uint64_t *labels, size_t n, size_t keep,
                    int features, uint64_t seed, size_t repeats,
                    double *sum, double *sum2, double *delta, double *delta2) {
    if (!n || !keep || features<1 || features>64 || !repeats) return 0;
    if (keep>n) keep=n;
    uint32_t *idx=malloc(keep*sizeof(uint32_t)); double *adjusted=malloc(keep*sizeof(double));
    if (!idx || !adjusted) {free(idx);free(adjusted);return 0;}
    memset(sum,0,(size_t)4*features*sizeof(double)); memset(sum2,0,(size_t)4*features*sizeof(double));
    memset(delta,0,(size_t)features*sizeof(double)); memset(delta2,0,(size_t)features*sizeof(double));
    for (size_t trial=0;trial<repeats;++trial) {
        double cutoff, old_total=0,new_total=0, old[64]={0}, corrected[64]={0};
        if (astra_cap_draw(logw,n,keep,&seed,0,idx,adjusted,&cutoff)!=(int)keep) return 0;
        for (size_t j=0;j<keep;++j) {
            const double w=exp((double)logw[idx[j]]),v=exp(adjusted[j]);
            old_total+=w;new_total+=v;
            for (int f=0;f<features;++f) if (labels[idx[j]] & (UINT64_C(1)<<f)) {old[f]+=w;corrected[f]+=v;}
        }
        for (int f=0;f<features;++f) {
            const double values[]={old[f],corrected[f],old[f]/old_total,corrected[f]/new_total};
            for (int m=0;m<4;++m) {
                const int o=m*features+f;sum[o]+=values[m];sum2[o]+=values[m]*values[m];
            }
            const double d=values[3]-values[2];delta[f]+=d;delta2[f]+=d*d;
        }
    }
    free(idx);free(adjusted);return 1;
}

#ifdef ASTRA_CAP_MAIN
int main(void) {
    const float w[]={-0.22314355f,-1.89711998f,-2.99573227f,-5.f,-8.f,-12.f};
    for (uint64_t seed=1;seed<101;++seed) {
        if (!astra_native_shrink_verify(w,6,3,seed)) return 1;
        uint64_t a=seed,b=seed;uint32_t ia[3],ib[3];double wa[3],wb[3],ta,tb;
        if (astra_cap_draw(w,6,3,&a,0,ia,wa,&ta)!=3 || astra_cap_draw(w,6,3,&b,1,ib,wb,&tb)!=3) return 2;
        if (a!=b || ta!=tb || memcmp(ia,ib,sizeof ia) || memcmp(wa,wb,sizeof wa)) return 3;
    }
    for (int d=-1000;d<=1000;++d) if (!isfinite(cap_corrected_logweight(-2,(double)d+2))) return 4;
    puts("Native parity, cutoff and numeric smoke checks pass.");return 0;
}
#endif
