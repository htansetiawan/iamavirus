/* Finite-state resampling with known marginal inclusion probabilities.
 * Find lambda with sum min(1,w_i/lambda)=k. Keep heavy states exactly;
 * systematic-sample the remaining states, assigning each weight lambda.
 * E[retained_i * output_weight_i] = w_i, before float32 storage.
 * Fearnhead & Clifford (2003), doi:10.1111/1467-9868.00421.
 * This independently written implementation uses O(n log n) time/O(n) memory.
 */
#include "m4_finite_resample.h"
#include <math.h>
#include <stdlib.h>

typedef struct { float logw; uint32_t index; } WeightRank;
static int descending(const void *a, const void *b) {
    const WeightRank *x=a, *y=b;
    if(x->logw!=y->logw)return x->logw>y->logw?-1:1;
    return x->index<y->index?-1:x->index>y->index;
}
static long double logadd(long double a,long double b) {
    if(isinf(b)&&b<0)return a;
    return a+log1pl(expl(b-a)); /* sorted a>=b */
}
int m4_finite_resample(const float *logw,size_t n,size_t k,double offset,
                       uint32_t *chosen,float *out_logw) {
    if(!logw||!chosen||!out_logw||!k||k>n||n>UINT32_MAX||
       !isfinite(offset)||offset<0||offset>=1)return -1;
    for(size_t i=0;i<n;++i)if(!isfinite(logw[i]))return -1;
    if(k==n){for(size_t i=0;i<n;++i){chosen[i]=(uint32_t)i;out_logw[i]=logw[i];}return 0;}
    WeightRank *rank=malloc(n*sizeof(*rank));
    long double *suffix=malloc((n+1)*sizeof(*suffix));
    unsigned char *heavy=calloc(n,1);
    if(!rank||!suffix||!heavy){free(rank);free(suffix);free(heavy);return -1;}
    for(size_t i=0;i<n;++i)rank[i]=(WeightRank){logw[i],(uint32_t)i};
    qsort(rank,n,sizeof(*rank),descending);
    suffix[n]=-INFINITY;
    for(size_t i=n;i-->0;) {
        long double a=rank[i].logw,b=suffix[i+1];
        suffix[i]=a>=b?logadd(a,b):logadd(b,a);
    }
    size_t h=0;
    while(h+1<k && (long double)rank[h].logw>suffix[h]-logl((long double)(k-h)))++h;
    for(size_t i=0;i<h;++i){
        chosen[i]=rank[i].index;out_logw[i]=rank[i].logw;heavy[rank[i].index]=1;
    }
    /* Rescale the tail independently: do not subtract its mass from a nearly
     * equal heavy total. This also supports log-weight ranges > exp's range. */
    const long double scale=rank[h].logw;
    long double z=0;
    for(size_t i=0;i<n;++i)if(!heavy[i])z+=expl((long double)logw[i]-scale);
    const size_t remainder=k-h;
    const long double step=z/(long double)remainder;
    const float loglambda=(float)(scale+logl(step));
    size_t got=h;long double cumulative=0;
    for(size_t i=0;i<n;++i)if(!heavy[i]) {
        cumulative+=expl((long double)logw[i]-scale);
        long double point=((long double)offset+(long double)(got-h))*step;
        /* Multiplication can round the last open-interval point to z. */
        if(got<k && point>=z)point=nextafterl(z,0);
        if(got<k && point<cumulative){chosen[got]=(uint32_t)i;out_logw[got++]=loglambda;}
    }
    free(rank);free(suffix);free(heavy);
    return got==k?0:-1;
}
