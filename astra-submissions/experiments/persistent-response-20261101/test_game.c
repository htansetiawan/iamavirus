/* Independent explicit latent-mode Kuhn construction with shared own infosets. */
#include <assert.h>
#include <string.h>
#include "cfr.h"
#include "mode.h"
static int terminal(Game *g,double v){return game_node(g,NODE_TERMINAL,0,-1,v);}

/* out: our12 action probs, free opponent12, fixed opponent12, value,
 *  same-game fixed-q utility, same-game free utility, nodes, infosets. */
void persistent_kuhn(double p,const double *q,int iterations,double *out) {
    Game g;game_init(&g);int ours[3][2],opponent[2][3][2];
    for(int card=0;card<3;++card)for(int stage=0;stage<2;++stage)ours[card][stage]=game_infoset(&g,0,2);
    for(int mode=0;mode<2;++mode)for(int card=0;card<3;++card)for(int stage=0;stage<2;++stage)opponent[mode][card][stage]=game_infoset(&g,1,2);
    int root=game_node(&g,NODE_CHANCE,0,-1,0),branches[12],n=0;double weights[12];
    /* Keep both modes even at endpoints, to test zero-reach handling. */
    for(int mode=0;mode<2;++mode)for(int c0=0;c0<3;++c0)for(int c1=0;c1<3;++c1) {
        if(c0==c1)continue;double win=c0>c1?1:-1;
        int own=game_node(&g,NODE_PLAYER,0,ours[c0][0],0);
        int after_check=game_node(&g,NODE_PLAYER,1,opponent[mode][c1][0],0);
        int after_bet=game_node(&g,NODE_PLAYER,1,opponent[mode][c1][1],0);
        int after_check_bet=game_node(&g,NODE_PLAYER,0,ours[c0][1],0);
        int cb[]={terminal(&g,-1),terminal(&g,2*win)};game_children(&g,after_check_bet,cb,NULL,2);
        int c[]={terminal(&g,win),after_check_bet};game_children(&g,after_check,c,NULL,2);
        int b[]={terminal(&g,1),terminal(&g,2*win)};game_children(&g,after_bet,b,NULL,2);
        int a[]={after_check,after_bet};game_children(&g,own,a,NULL,2);
        branches[n]=own;weights[n++]=persistent_weight(p,mode)/6;
    }
    assert(n==12);game_children(&g,root,branches,weights,n);game_finalize(&g);
    for(int card=0;card<3;++card)for(int stage=0;stage<2;++stage)game_restrict(&g,opponent[1][card][stage],1,q+4*card+2*stage);
    for(int t=1;t<=iterations;++t)pcfr_iteration(&g,t);
    double x[36];assert(g.n_slots==36);pcfr_current(&g,x);memcpy(out,x,sizeof(x));out[36]=game_value(&g,x);
    for(int i=0;i<12;++i)g.prob[g.nodes[root].first+i]=i<6?0:1.0/6;out[37]=game_value(&g,x);
    for(int i=0;i<12;++i)g.prob[g.nodes[root].first+i]=i<6?1.0/6:0;out[38]=game_value(&g,x);
    out[39]=g.n_nodes;out[40]=g.n_infosets;game_free(&g);
}

static int trap_chain(Game *g,int depth,int remaining,double confidence) {
    if(!remaining)return terminal(g,-1);
    int I=game_infoset(g,1,2);double q[]={1,0};game_restrict(g,I,confidence,q);
    int node=game_node(g,NODE_PLAYER,1,I,0),kids[]={terminal(g,1),trap_chain(g,depth,remaining-1,confidence)};
    game_children(g,node,kids,NULL,2);return node;
}

void persistent_trap(int depth,double p,int local,int iterations,double *out) {
    Game g;game_init(&g);int root=game_node(&g,NODE_CHANCE,0,-1,0),own=game_infoset(&g,0,2);
    int kids[2],n=local?1:persistent_count(p);double weights[2];
    for(int i=0;i<n;++i) {
        int mode=local?0:persistent_mode(p,i);kids[i]=game_node(&g,NODE_PLAYER,0,own,0);
        int a[]={terminal(&g,0),trap_chain(&g,depth,depth,local?p:(double)mode)};game_children(&g,kids[i],a,NULL,2);
        weights[i]=local?1:persistent_weight(p,mode);
    }
    game_children(&g,root,kids,weights,n);game_finalize(&g);
    for(int t=1;t<=iterations;++t)pcfr_iteration(&g,t);
    double x[128];assert(g.n_slots<=128);pcfr_current(&g,x);out[0]=x[0];out[1]=x[1];out[2]=game_value(&g,x);
    x[0]=0;x[1]=1;out[3]=game_value(&g,x);out[4]=g.n_nodes;game_free(&g);
}
