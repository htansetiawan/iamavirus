#include <stdio.h>
#include "br.h"

static double payoff(int seed,int w,int a,int b,int c,int d) {
    unsigned n=(unsigned)(1+seed*1721+w*983+a*617+b*227+c*83+d*37);
    n^=n>>3;n*=2654435761u;n^=n>>11;return (double)(n%2001)/1000-1;
}
static int leaf(Game *g,double v){return game_node(g,NODE_TERMINAL,0,-1,v);}
static int node(Game *g,int I){return game_node(g,NODE_PLAYER,g->is_player[I],I,0);}

int main(int argc,char **argv) {
    int invalid=argc>1;printf("[");
    for(int seed=0;seed<6;++seed) {
        Game g;game_init(&g);int root=game_node(&g,NODE_CHANCE,0,-1,0);
        int R=game_infoset(&g,0,2),O=game_infoset(&g,1,2),next[2][2][2],last[2][2];
        for(int a=0;a<2;++a)for(int b=0;b<2;++b)for(int v=0;v<2;++v)next[a][b][v]=game_infoset(&g,0,2);
        for(int b=0;b<2;++b)for(int v=0;v<2;++v)last[b][v]=game_infoset(&g,1,2);
        int world[4];double chance[4]={.1,.2,.3,.4};if(seed==5){chance[0]=0;chance[3]=.5;}
        for(int w=0;w<4;++w) {
            world[w]=node(&g,R);int aa[2];
            for(int a=0;a<2;++a) {
                aa[a]=node(&g,O);int bb[2];
                for(int b=0;b<2;++b) {
                    bb[b]=node(&g,next[a][b][w%2]);int cc[2];
                    for(int c=0;c<2;++c) {
                        cc[c]=node(&g,last[invalid?0:b][w%2]);int dd[2];
                        for(int d=0;d<2;++d)dd[d]=leaf(&g,payoff(seed,w,a,b,c,d));
                        game_children(&g,cc[c],dd,NULL,2);
                    }
                    game_children(&g,bb[b],cc,NULL,2);
                }
                game_children(&g,aa[a],bb,NULL,2);
            }
            game_children(&g,world[w],aa,NULL,2);
        }
        game_children(&g,root,world,chance,4);game_finalize(&g);
        double cs[]={0,.25,.75,1,.25,.25};
        for(int I=0;I<g.n_infosets;++I)if(g.is_player[I]==1){double p[2]={I==O?.2:.7,I==O?.8:.3};game_restrict(&g,I,cs[seed],p);}
        double *x=malloc(g.n_slots*sizeof(double)),*reply=malloc(g.n_slots*sizeof(double)),*v=malloc(g.n_nodes*sizeof(double));
        for(int I=0;I<g.n_infosets;++I){double p=((I+seed)%7+1)/9.0;if(I==R&&seed>=4)p=seed==4?0:1;for(int a=0;a<2;++a)x[g.is_offset[I]+a]=(1-g.confidence[I])*(a?1-p:p)+(g.confidence[I]>0?g.confidence[I]*g.fixed_policy[g.is_offset[I]+a]:0);}
        printf("%s{\"seed\":%d,\"root\":%d,\"infosets\":[",seed?",":"",seed,root);
        for(int I=0;I<g.n_infosets;++I)printf("%s{\"player\":%d,\"offset\":%d,\"count\":2,\"confidence\":%.17g,\"q\":[%.17g,%.17g]}",I?",":"",g.is_player[I],g.is_offset[I],g.confidence[I],g.fixed_policy[g.is_offset[I]],g.fixed_policy[g.is_offset[I]+1]);
        printf("],\"x\":[");for(int s=0;s<g.n_slots;++s)printf("%s%.17g",s?",":"",x[s]);printf("],\"nodes\":[");
        for(int id=0;id<g.n_nodes;++id){const GameNode *n=&g.nodes[id];printf("%s{\"type\":%d,\"player\":%d,\"infoset\":%d,\"value\":%.17g,\"children\":[",id?",":"",n->type,n->player,n->infoset,n->value);for(int a=0;a<n->count;++a)printf("%s%d",a?",":"",g.child[n->first+a]);printf("],\"chance\":[");for(int a=0;a<n->count;++a)printf("%s%.17g",a?",":"",g.prob[n->first+a]);printf("]}");}
        printf("],\"solutions\":[");
        for(int player=0;player<2;++player){BrIndex index=br_index(&g,player);for(int mode=0;mode<3;++mode){double value=br_solve(&g,&index,x,mode,reply,v);printf("%s{\"player\":%d,\"mode\":%d,\"value\":%.17g,\"strategy\":[",player||mode?",":"",player,mode,value);for(int s=0;s<g.n_slots;++s)printf("%s%.17g",s?",":"",reply[s]);printf("]}");}br_index_free(&index);}
        printf("],\"original_value\":%.17g}",game_value(&g,x));free(x);free(reply);free(v);game_free(&g);
    }
    puts("]");return 0;
}
