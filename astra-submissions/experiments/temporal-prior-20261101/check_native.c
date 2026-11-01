#define _POSIX_C_SOURCE 200809L
#include "inference.h"
#include <math.h>
#include <stdio.h>
#include <time.h>
#include <assert.h>

static double seconds(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static double lp(const float *z,int n,int played) {
    double top=-INFINITY;for(int i=0;i<n;++i)if(z[i]>top)top=z[i];
    double sum=0;for(int i=0;i<n;++i)sum+=exp(z[i]-top);
    return z[played]-top-log(sum);
}
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    FILE *in=fopen(argv[1],"r");if(!in)return 2;
    fow_init();Position p;TemporalHistory history={0};Move previous=0;
    int game=-1,ply=0,ids[2]={-1,-1};long positions=0,actions=0;double elapsed[2]={0},sparse_error=0;
    char line[1024];
    while(fgets(line,sizeof(line),in)) {
        if(!strncmp(line,"game ",5)) {
            assert(sscanf(line+5,"%d %d %d",&game,&ids[0],&ids[1])==3);
            pos_start(&p);memset(&history,0,sizeof(history));previous=0;ply=0;continue;
        }
        char uci[8];assert(sscanf(line,"%7s",uci)==1);if(!strcmp(uci,"initial"))continue;
        MoveList l;generate_moves(&p,&l);int played=-1;
        for(int i=0;i<l.count;++i){char u[6];move_to_uci(l.moves[i],u);if(!strcmp(u,uci))played=i;}
        assert(played>=0);
        if(ids[p.side]>=0) {
            float z[2][256];
            for(int j=0;j<2;++j){int arm=(j+(int)positions)%2;double start=seconds();
                temporal_logits(&history,&p,&l,previous,arm,z[arm]);elapsed[arm]+=seconds()-start;}
            /* Independent dense definition vs sparse inference on every action. */
            for(int i=0;i<l.count;++i){float x[TP_FEATURES];temporal_features(&history,&p,l.moves[i],x);
                double dense=0;for(int k=0;k<TP_FEATURES;++k)dense+=x[k]*learned_temporal[MM_FEATURES+k];
                double delta=fabs(dense-temporal_sparse_score(learned_temporal+MM_FEATURES,&history,&p,l.moves[i]));
                if(delta>sparse_error)sparse_error=delta;
                assert(delta<1e-5);}
            printf("%d %d %d %.12g %.12g\n",game,ply,p.side,lp(z[0],l.count,played),lp(z[1],l.count,played));
            positions++;actions+=l.count;
        }
        temporal_advance(&history,&p,l.moves[played]);previous=l.moves[played];Undo u;make_move(&p,l.moves[played],&u);ply++;
    }
    fprintf(stderr,"{\"positions\":%ld,\"actions\":%ld,\"static_seconds\":%.9g,\"temporal_seconds\":%.9g,\"dense_sparse_max_error\":%.9g}\n",positions,actions,elapsed[0],elapsed[1],sparse_error);
    fclose(in);return 0;
}
