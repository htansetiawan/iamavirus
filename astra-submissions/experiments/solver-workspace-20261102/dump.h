/* Offline, after the original move selection; no privileged game input. */
#include <assert.h>
#include <stdio.h>
static void dump_write(const void *p,size_t width,size_t count,FILE *f){assert(fwrite(p,width,count,f)==count);}
static void solver_dump(const Game *g){
 const char *path=getenv("ASTRA_SOLVER_TREE");if(!path)return;
 FILE *f=fopen(path,"wbx");assert(f);assert(g->n_pending==0);
 dump_write("ASTRA253",1,8,f);int dims[]={g->n_nodes,g->n_edges,g->n_infosets,g->n_slots,g->root};dump_write(dims,sizeof(int),5,f);
 for(int i=0;i<g->n_nodes;++i){const GameNode *n=&g->nodes[i];int fields[]={n->type,n->player,n->infoset,n->first,n->count};dump_write(fields,sizeof(int),5,f);dump_write(&n->value,sizeof(double),1,f);}
 dump_write(g->child,sizeof(int),g->n_edges,f);dump_write(g->prob,sizeof(double),g->n_edges,f);
 dump_write(g->is_player,sizeof(int),g->n_infosets,f);dump_write(g->is_actions,sizeof(int),g->n_infosets,f);dump_write(g->is_offset,sizeof(int),g->n_infosets,f);
 dump_write(g->regret,sizeof(double),g->n_slots,f);dump_write(g->last,sizeof(double),g->n_slots,f);dump_write(g->strategy_sum,sizeof(double),g->n_slots,f);
 assert(!ferror(f));assert(fclose(f)==0);
}
