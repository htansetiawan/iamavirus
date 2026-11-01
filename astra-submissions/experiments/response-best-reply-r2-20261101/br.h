/* Read-only, linear-time best response on a finite layered perfect-recall tree.
 * Utilities remain player 0's. No determinization: each information set gets
 * ONE response, selected by counterfactual reach across all its member nodes.
 * Layering and the responding player's recall are checked, not presumed.
 */
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "cfr.h"

typedef struct {
    int *order, *depth, *start, layers;
    int *iprev, *iaction, *idepth;
    int player;
} BrIndex;

static BrIndex br_index(const Game *g, int player) {
    BrIndex b={0}; b.player=player;
    b.order=malloc((size_t)g->n_nodes*sizeof(int));
    b.depth=malloc((size_t)g->n_nodes*sizeof(int));
    b.start=calloc((size_t)g->n_nodes+2,sizeof(int));
    b.iprev=malloc((size_t)g->n_infosets*sizeof(int));
    b.iaction=malloc((size_t)g->n_infosets*sizeof(int));
    b.idepth=malloc((size_t)g->n_infosets*sizeof(int));
    int *prev=malloc((size_t)g->n_nodes*sizeof(int));
    int *action=malloc((size_t)g->n_nodes*sizeof(int));
    assert(b.order&&b.depth&&b.start&&b.iprev&&b.iaction&&b.idepth&&prev&&action);
    for(int i=0;i<g->n_nodes;++i)b.depth[i]=-1;
    for(int i=0;i<g->n_infosets;++i)b.idepth[i]=-1;
    b.order[0]=g->root;b.depth[g->root]=0;prev[g->root]=action[g->root]=-1;
    int tail=1;
    for(int at=0;at<tail;++at) {
        int id=b.order[at],d=b.depth[id]; const GameNode *n=&g->nodes[id];
        ++b.start[d+1];if(d+1>b.layers)b.layers=d+1;
        assert(n->type==NODE_CHANCE||n->type==NODE_PLAYER||n->type==NODE_TERMINAL);
        if(n->type==NODE_TERMINAL){assert(n->count==0);continue;}
        assert(n->count>0 && n->first>=0 && n->first+n->count<=g->n_edges);
        if(n->type==NODE_PLAYER) {
            int I=n->infoset;assert(I>=0&&I<g->n_infosets&&g->is_player[I]==n->player&&g->is_actions[I]==n->count);
            if(b.idepth[I]<0){b.idepth[I]=d;b.iprev[I]=prev[id];b.iaction[I]=action[id];}
            else {assert(b.idepth[I]==d);if(n->player==player)assert(b.iprev[I]==prev[id]&&b.iaction[I]==action[id]);}
        }
        double chance_sum=0;
        for(int a=0;a<n->count;++a) {
            int child=g->child[n->first+a];assert(child>=0&&child<g->n_nodes&&b.depth[child]<0);
            b.depth[child]=d+1;b.order[tail++]=child;
            prev[child]=n->type==NODE_PLAYER&&n->player==player?n->infoset:prev[id];
            action[child]=n->type==NODE_PLAYER&&n->player==player?a:action[id];
            if(n->type==NODE_CHANCE){assert(g->prob[n->first+a]>=0);chance_sum+=g->prob[n->first+a];}
        }
        if(n->type==NODE_CHANCE)assert(fabs(chance_sum-1)<1e-9);
    }
    assert(tail==g->n_nodes);
    for(int d=1;d<=b.layers;++d)b.start[d]+=b.start[d-1];
    assert(b.start[b.layers]==g->n_nodes);
    free(prev);free(action);return b;
}

static void br_index_free(BrIndex *b) {
    free(b->order);free(b->depth);free(b->start);free(b->iprev);free(b->iaction);free(b->idepth);memset(b,0,sizeof(*b));
}

/* mode: 0 unrestricted, 1 original restriction at all responding infosets,
 * 2 restriction only at the first responding infoset on each history.
 * x is the fixed profile; output/value are separate caller-owned arrays.
 */
static double br_solve(const Game *g,const BrIndex *b,const double *x,int mode,double *output,double *value) {
    assert(mode>=0&&mode<=2);memcpy(output,x,(size_t)g->n_slots*sizeof(double));
    double *reach=calloc(g->n_nodes,sizeof(double)),*q=calloc(g->n_slots,sizeof(double));
    unsigned char *done=calloc(g->n_infosets,1);assert(reach&&q&&done);reach[g->root]=1;
    for(int at=0;at<g->n_nodes;++at) {
        int id=b->order[at];const GameNode *n=&g->nodes[id];
        if(n->type==NODE_TERMINAL){value[id]=n->value;continue;}
        double sum=0;
        for(int a=0;a<n->count;++a) {
            double p=n->type==NODE_CHANCE?g->prob[n->first+a]:x[g->is_offset[n->infoset]+a];
            assert(p>=-1e-10 && p<=1+1e-10);sum+=p;
            /* Responding player's own reach is excluded, including restrictions. */
            reach[g->child[n->first+a]]=reach[id]*(n->type==NODE_PLAYER&&n->player==b->player?1:p);
        }
        assert(fabs(sum-1)<1e-8);
    }
    for(int d=b->layers-1;d>=0;--d) {
        for(int at=b->start[d];at<b->start[d+1];++at) {
            int id=b->order[at];const GameNode *n=&g->nodes[id];
            if(n->type==NODE_TERMINAL)continue;
            if(n->type==NODE_PLAYER&&n->player==b->player) {
                int o=g->is_offset[n->infoset];
                for(int a=0;a<n->count;++a)q[o+a]+=reach[id]*value[g->child[n->first+a]];
            } else {
                value[id]=0;
                for(int a=0;a<n->count;++a)value[id]+=(n->type==NODE_CHANCE?g->prob[n->first+a]:x[g->is_offset[n->infoset]+a])*value[g->child[n->first+a]];
            }
        }
        for(int at=b->start[d];at<b->start[d+1];++at) {
            int id=b->order[at];const GameNode *n=&g->nodes[id];
            if(n->type!=NODE_PLAYER||n->player!=b->player)continue;
            int I=n->infoset,o=g->is_offset[I];
            if(!done[I]) {
                int best=0;
                for(int a=1;a<n->count;++a)if(b->player==0?q[o+a]>q[o+best]:q[o+a]<q[o+best])best=a;
                double c=(mode==1||(mode==2&&b->iprev[I]<0))?g->confidence[I]:0;
                assert(c>=0&&c<=1);double total=0;
                for(int a=0;a<n->count;++a){output[o+a]=(c>0?c*g->fixed_policy[o+a]:0)+(a==best?1-c:0);total+=output[o+a];}
                assert(fabs(total-1)<1e-8);done[I]=1;
            }
            value[id]=0;
            for(int a=0;a<n->count;++a)value[id]+=output[o+a]*value[g->child[n->first+a]];
        }
    }
    double v=value[g->root];assert(fabs(v-game_value(g,output))<1e-8);
    free(reach);free(q);free(done);return v;
}
