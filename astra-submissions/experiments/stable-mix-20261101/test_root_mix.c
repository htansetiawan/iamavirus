#define _POSIX_C_SOURCE 200809L
#include "root_mix.h"

int main(int argc, char **argv) {
    (void)argv;
    RootMixTrack t; memset(&t,0,sizeof(t));
    double x[5]={.4,.3,.2,.1,0}, p[5], copy[5]; memcpy(copy,x,sizeof(x));
    if (argc>1) {
        for(int i=0;i<32;++i) {double probability;printf("%d",root_mix_pick(&t,x,5,1,&probability));}
        putchar('\n');return 0;
    }
    root_mix_observe(&t,x,5,.49,1);assert(t.observations==0);
    assert(root_mix_probs(&t,x,5,2,p)==0 && p[0]==1 && p[1]==0);
    root_mix_observe(&t,x,5,.5,1);
    double absent[5]={.7,0,.2,.1,0};root_mix_observe(&t,absent,5,.6,1);
    root_mix_observe(&t,x,5,.7,1);assert(t.observations==3 && !t.stable[1]);
    root_mix_probs(&t,x,5,2,p);
    assert(fabs(p[0]-.8)<1e-12 && p[1]==0 && fabs(p[2]-.2)<1e-12 && p[3]==0 && p[4]==0);
    assert(memcmp(copy,x,sizeof(x))==0); /* execution policy never mutates the solver */
    assert(root_mix_at_quantile(p,5,0)==0 && root_mix_at_quantile(p,5,.8)==2);
    assert(root_mix_at_quantile(p,5,nextafter(1,0))==2);
    memset(&t,0,sizeof(t));root_mix_observe(&t,x,5,.5,1);root_mix_probs(&t,x,5,2,p);
    assert(fabs(p[0]-.5)<1e-12 && fabs(p[1]-.3)<1e-12 && fabs(p[2]-.2)<1e-12 && p[3]==0);
    root_mix_probs(&t,x,5,0,p);assert(p[0]==1 && p[1]==0);
    root_mix_probs(&t,x,5,1,p);
    int grid[5]={0};for(int i=0;i<10000;++i)++grid[root_mix_at_quantile(p,5,(i+.5)/10000.0)];
    assert(grid[0]==4000 && grid[1]==3000 && grid[2]==2000 && grid[3]==1000 && grid[4]==0);
    uint64_t rng=123, repeat=123;int counts[5]={0};
    for(int i=0;i<1000000;++i) {
        uint64_t a=root_mix_random(&rng),b=root_mix_random(&repeat);assert(a==b);
        ++counts[root_mix_at_quantile(p,5,(a>>11)*(1.0/9007199254740992.0))];
    }
    for(int i=0;i<5;++i)assert(fabs(counts[i]/1000000.0-x[i])<.002);
    /* Rock-paper-scissors: the same uniform strategy has worst-case payoff
       zero when executed, -1 after deterministic argmax tie breaking. */
    double rps[3]={1.0/3,1.0/3,1.0/3}, mixed[3], pure[3];
    memset(&t,0,sizeof(t));root_mix_observe(&t,rps,3,1,1);
    root_mix_probs(&t,rps,3,2,mixed);root_mix_probs(&t,rps,3,0,pure);
    double payoffs[3][3]={{0,-1,1},{1,0,-1},{-1,1,0}}, worst_m=1,worst_p=1;
    for(int j=0;j<3;++j) {double vm=0,vp=0;for(int i=0;i<3;++i){vm+=mixed[i]*payoffs[i][j];vp+=pure[i]*payoffs[i][j];}
        if(vm<worst_m)worst_m=vm;if(vp<worst_p)worst_p=vp;}
    assert(fabs(worst_m)<1e-12 && worst_p==-1);
    printf("{\"grid\":[%d,%d,%d,%d,%d],\"random_counts\":[%d,%d,%d,%d,%d],\"rps_mixed_worst\":%.17g,\"rps_pure_worst\":%.17g}\n",
        grid[0],grid[1],grid[2],grid[3],grid[4],counts[0],counts[1],counts[2],counts[3],counts[4],worst_m,worst_p);
    return 0;
}
