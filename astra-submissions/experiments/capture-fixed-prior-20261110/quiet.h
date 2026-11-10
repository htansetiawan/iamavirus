/* Conditional quiet-move residual. Existing capture logits AND the original
 * native global log normalizer are unchanged. Not an arena safety guarantee. */
#ifndef ASTRA_QUIET_H
#define ASTRA_QUIET_H
#include <math.h>
#include <string.h>

static const int astra_quiet_columns[22]={3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25};

/* x: row-major n x26, base: original unnormalized native logits.
 * F=14 (cheap) or22 (full). Export float log-likelihoods, leaving captures
 * bit-identical to base-old_log_z. A deployment hook must KEEP old_log_z;
 * recomputing a new normalizer would weaken that numerical identity. */
static void astra_quiet_logp(const float *x,const float *base,int n,int F,
        const float *linear,const float *quadratic,float *out) {
    float top=-INFINITY;
    for(int j=0;j<n;++j)if(base[j]>top)top=base[j];
    double sum=0;
    for(int j=0;j<n;++j)sum+=exp((double)(base[j]-top));
    const float old_log_z=top+(float)log(sum);
    for(int j=0;j<n;++j)out[j]=base[j]-old_log_z;
    float delta[256];double old_top=-INFINITY,new_top=-INFINITY;
    int quiet=0,changed=0;
    for(int r=0;r<n;++r){
        delta[r]=0;
        if(x[r*26]>0)continue;
        int active[22],count=0;float values[22];
        for(int a=0;a<F;++a){
            float v=x[r*26+astra_quiet_columns[a]];values[a]=v;
            if(v!=0){active[count++]=a;delta[r]+=linear[a]*v;}
        }
        for(int a=0;a<count;++a)for(int b=a;b<count;++b){
            int i=active[a],j=active[b];delta[r]+=quadratic[F*i+j]*values[i]*values[j];
        }
        ++quiet;changed|=delta[r]!=0;
        if(base[r]>old_top)old_top=base[r];
        double z=(double)base[r]+delta[r];if(z>new_top)new_top=z;
    }
    if(quiet<=1 || !changed)return;
    double old_sum=0,new_sum=0;
    for(int r=0;r<n;++r)if(x[r*26]==0){
        old_sum+=exp((double)base[r]-old_top);
        new_sum+=exp((double)base[r]+delta[r]-new_top);
    }
    const double correction=old_top+log(old_sum)-new_top-log(new_sum);
    for(int r=0;r<n;++r)if(x[r*26]==0)
        out[r]=(float)((double)base[r]+delta[r]+correction-old_log_z);
}
#endif
