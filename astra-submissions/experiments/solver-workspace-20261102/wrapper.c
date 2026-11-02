#include "cfr.h"
#include "api.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
static void *create(void){Game *g=malloc(sizeof(*g));game_init(g);return g;}
static void destroy(void *p){game_free(p);free(p);}
static int info(void *p,int player,int n){return game_infoset(p,player,n);}
static int node(void *p,int type,int player,int I,double v){return game_node(p,type,player,I,v);}
static void children(void *p,int node,const int *kids,const double *prob,int n){game_children(p,node,kids,prob,n);}
static void finalize(void *p){game_finalize(p);}
static void grow(void *p){game_grow(p);}
static void start(void *p,int I,int a){game_start_on(p,I,a);}
static void expand(void *p,int id,int player,int I,const int *kids,int n){game_expand_leaf(p,id,player,I,kids,n);}
static void step(void *p,int t){pcfr_iteration(p,t);}
static size_t state(void *p,double *out){Game *g=p;size_t n=g->n_slots;if(out){memcpy(out,g->regret,n*8);memcpy(out+n,g->last,n*8);memcpy(out+2*n,g->strategy_sum,n*8);pcfr_current(g,out+3*n);}return 4*n;}
static void value(void *p,int id,double v){((Game*)p)->nodes[id].value=v;}
static size_t storage(void *p){Game *g=p;
#if FAST
 return (size_t)g->allocated_slots*5*sizeof(double);
#else
 return (size_t)g->finalized_slots*4*sizeof(double);
#endif
}
static void read_exact(void *p,size_t size,size_t count,FILE *f){assert(fread(p,size,count,f)==count);}
static void *load(const char *path){
 FILE *f=fopen(path,"rb");assert(f);char magic[8];read_exact(magic,1,8,f);assert(!memcmp(magic,"ASTRA253",8));
 int dims[5];read_exact(dims,sizeof(int),5,f);for(int i=0;i<4;++i)assert(dims[i]>=0&&dims[i]<=10000000);
 Game *g=create();g->n_nodes=g->cap_nodes=dims[0];g->n_edges=g->cap_edges=dims[1];g->n_infosets=g->cap_infosets=dims[2];g->n_slots=dims[3];g->root=dims[4];
 g->nodes=calloc((size_t)g->n_nodes,sizeof(GameNode));assert(g->nodes);
 for(int i=0;i<g->n_nodes;++i){int fields[5];double value;read_exact(fields,sizeof(int),5,f);read_exact(&value,sizeof(double),1,f);GameNode *n=&g->nodes[i];n->type=fields[0];n->player=fields[1];n->infoset=fields[2];n->first=fields[3];n->count=fields[4];n->value=value;assert(n->first>=0&&n->first+n->count<=g->n_edges);}
 g->child=malloc(g->n_edges*sizeof(int));g->prob=malloc(g->n_edges*sizeof(double));read_exact(g->child,sizeof(int),g->n_edges,f);read_exact(g->prob,sizeof(double),g->n_edges,f);
 g->is_player=malloc(g->n_infosets*sizeof(int));g->is_actions=malloc(g->n_infosets*sizeof(int));g->is_offset=malloc(g->n_infosets*sizeof(int));
 read_exact(g->is_player,sizeof(int),g->n_infosets,f);read_exact(g->is_actions,sizeof(int),g->n_infosets,f);read_exact(g->is_offset,sizeof(int),g->n_infosets,f);
 game_finalize(g);read_exact(g->regret,sizeof(double),g->n_slots,f);read_exact(g->last,sizeof(double),g->n_slots,f);read_exact(g->strategy_sum,sizeof(double),g->n_slots,f);assert(fgetc(f)==EOF);fclose(f);return g;
}
const SolverAPI API_NAME={create,destroy,info,node,children,finalize,grow,start,expand,step,state,value,storage,load};
