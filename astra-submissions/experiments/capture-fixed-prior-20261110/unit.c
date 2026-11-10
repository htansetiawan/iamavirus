#include "quiet.h"
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
static uint64_t rng=2931100;
static float random_float(void){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return (float)(rng%100001)/50000-1;}
int main(void){
    long captures=0,rows=0;
    for(int F=14;F<=22;F+=8)for(int trial=0;trial<1000;++trial){
        int n=1+trial%255;float x[256*26]={0},base[256],lin[22]={0},q[22*22]={0},old[256],next[256];
        for(int j=0;j<n;++j){base[j]=random_float()*(trial%3==0?1000:8);
            for(int k=0;k<26;++k)x[26*j+k]=random_float();
            x[26*j]=(trial%5==0 || (trial%5>1 && j%3==0))?1:0;}
        astra_quiet_logp(x,base,n,F,lin,q,old);
        astra_quiet_logp(x,base,n,F,lin,q,next);assert(!memcmp(old,next,n*sizeof(float)));
        for(int i=0;i<F;++i){lin[i]=random_float()*.1f;for(int j=i;j<F;++j)q[i*F+j]=random_float()*.1f;}
        astra_quiet_logp(x,base,n,F,lin,q,next);
        double before=0,after=0;
        for(int j=0;j<n;++j){assert(isfinite(next[j]));
            if(x[26*j]>0){assert(!memcmp(old+j,next+j,sizeof(float)));++captures;}
            else {before+=exp((double)old[j]);after+=exp((double)next[j]);}
            ++rows;}
        assert(fabs(before-after)<2e-4);
    }
    printf("capture-fixed units: %ld capture logp bits unchanged, %ld action rows; zero identity, no quiet, all quiet, singleton, extreme logits\n",captures,rows);
    return 0;
}
