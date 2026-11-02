#include "api.h"
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {void *b,*f;int *leaves,n,capacity,rootI,rootActions;} Pair;
static uint64_t rng=253;static size_t compared=0,checked_slots=0;
static double random_value(void){rng=rng*6364136223846793005ULL+1442695040888963407ULL;return (double)((rng>>11)%2000001)/1000000-1;}
static void leaf_add(Pair *p,int n){if(p->n==p->capacity){p->capacity=p->capacity?2*p->capacity:256;p->leaves=realloc(p->leaves,p->capacity*sizeof(int));assert(p->leaves);}p->leaves[p->n++]=n;}
static int node(Pair *p,int type,int player,int I,double value){int a=base_api.node(p->b,type,player,I,value),b=fast_api.node(p->f,type,player,I,value);assert(a==b);if(type==2)leaf_add(p,a);return a;}
static int info(Pair *p,int player,int count){int a=base_api.info(p->b,player,count),b=fast_api.info(p->f,player,count);assert(a==b);return a;}
static void children(Pair *p,int id,int *kids,double *prob,int n){base_api.children(p->b,id,kids,prob,n);fast_api.children(p->f,id,kids,prob,n);}
static void start(Pair *p,int I,int action){base_api.start(p->b,I,action);fast_api.start(p->f,I,action);}
static void grow(Pair *p){base_api.grow(p->b);fast_api.grow(p->f);}
static void compare(Pair *p){
 size_t n=base_api.state(p->b,NULL);assert(n==fast_api.state(p->f,NULL));
 double *a=malloc((n?n:1)*sizeof(double)),*b=malloc((n?n:1)*sizeof(double));assert(a&&b);
 base_api.state(p->b,a);fast_api.state(p->f,b);
 if(memcmp(a,b,n*sizeof(double))){for(size_t i=0;i<n;++i)if(memcmp(a+i,b+i,sizeof(double)))fprintf(stderr,"mismatch slot=%zu base=%.17g fast=%.17g\n",i,a[i],b[i]);abort();}
 compared++;checked_slots+=n;free(a);free(b);
}
static Pair build(int actions,int opponents,int uniform){
 Pair p={0};p.b=base_api.create();p.f=fast_api.create();
 int root=node(&p,0,0,-1,0);p.rootI=info(&p,0,actions);p.rootActions=actions;
 if(!uniform)start(&p,p.rootI,actions-1);
 int world_nodes[3];double weights[3]={.61,.39,0};
 int *later=malloc(actions*2*sizeof(int));
 for(int a=0;a<actions;++a)for(int signal=0;signal<2;++signal)later[2*a+signal]=info(&p,0,3);
 for(int w=0;w<3;++w){
  world_nodes[w]=node(&p,1,0,p.rootI,0);int I=info(&p,1,opponents);
  if(!uniform)start(&p,I,w%opponents);
  int *choices=malloc(actions*sizeof(int));
  for(int a=0;a<actions;++a){
   choices[a]=node(&p,1,1,I,0);int *reply=malloc(opponents*sizeof(int));
   for(int b=0;b<opponents;++b){
    int I2=later[2*a+b%2];reply[b]=node(&p,1,0,I2,0);int leaf[3];
    for(int c=0;c<3;++c)leaf[c]=node(&p,2,0,-1,random_value());
    children(&p,reply[b],leaf,NULL,3);
   }
   children(&p,choices[a],reply,NULL,opponents);free(reply);
  }
  children(&p,world_nodes[w],choices,NULL,actions);free(choices);
 }
 children(&p,root,world_nodes,weights,3);free(later);
 base_api.finalize(p.b);fast_api.finalize(p.f);compare(&p);return p;
}
static void add_branch(Pair *p,int step){
 assert(p->n);int id=p->leaves[--p->n];int count=2+step%7,player=step%2,I=info(p,player,count);int kids[16];
 for(int j=0;j<count;++j)kids[j]=node(p,2,0,-1,random_value());
 base_api.expand(p->b,id,player,I,kids,count);fast_api.expand(p->f,id,player,I,kids,count);
 if(step%3)start(p,I,step%count);grow(p);compare(p);
}
static void destroy(Pair *p){base_api.destroy(p->b);fast_api.destroy(p->f);free(p->leaves);}
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv){
 if(argc==4&&!strcmp(argv[1],"trace")){
  int steps=atoi(argv[3]);assert(steps>0&&steps<=10000);double bs=0,fs=0;size_t storage_b=0,storage_f=0;
  for(int repeat=0;repeat<6;++repeat){
   Pair p={0};p.b=base_api.load(argv[2]);p.f=fast_api.load(argv[2]);compare(&p);
   for(int order=0;order<2;++order){int fast=(order+repeat)%2;const SolverAPI *api=fast?&fast_api:&base_api;void *g=fast?p.f:p.b;double began=now();for(int t=1;t<=steps;++t)api->step(g,t);double elapsed=now()-began;if(repeat){if(fast)fs+=elapsed;else bs+=elapsed;}}
   compare(&p);storage_b=base_api.storage(p.b);storage_f=fast_api.storage(p.f);destroy(&p);
  }
  printf("{\"trace\":true,\"steps\":%d,\"timed_repeats\":5,\"base_seconds\":%.9f,\"fast_seconds\":%.9f,\"speedup\":%.6f,\"base_storage\":%zu,\"fast_storage\":%zu,\"identical\":true}\n",steps,bs,fs,bs/fs,storage_b,storage_f);return 0;
 }
 if(argc>1&&!strcmp(argv[1],"bench")){
  /* Synthetic timing is only a correctness/performance preflight. */
  Pair p=build(257,16,0);double base_seconds=0,fast_seconds=0;
  for(int batch=0;batch<10;++batch){
   for(int order=0;order<2;++order){int fast=(order+batch)%2;const SolverAPI *api=fast?&fast_api:&base_api;void *g=fast?p.f:p.b;double before=now();for(int j=1;j<=20;++j)api->step(g,batch*20+j);double elapsed=now()-before;if(fast)fast_seconds+=elapsed;else base_seconds+=elapsed;}
   compare(&p);
  }
  printf("{\"synthetic_only\":true,\"base_seconds\":%.9f,\"fast_seconds\":%.9f,\"speedup\":%.6f,\"base_storage\":%zu,\"fast_storage\":%zu}\n",base_seconds,fast_seconds,base_seconds/fast_seconds,base_api.storage(p.b),fast_api.storage(p.f));destroy(&p);return 0;
 }
 for(int seed=0;seed<32;++seed){
  Pair p=build(seed==31?257:2+seed%9,2+seed%5,seed%2);
  for(int t=1;t<=256;++t){
   if(t%11==0)add_branch(&p,t);
   if(t%13==0){start(&p,p.rootI,t%p.rootActions);grow(&p);compare(&p);}
   if(t%5==0){int id=p.leaves[p.n-1];double value=random_value();base_api.value(p.b,id,value);fast_api.value(p.f,id,value);}
   base_api.step(p.b,t);fast_api.step(p.f,t);compare(&p);
  }
  destroy(&p);
 }
 /* Zero-action terminal game; the cache must tolerate a zero logical size. */
 Pair terminal={0};terminal.b=base_api.create();terminal.f=fast_api.create();node(&terminal,2,0,-1,.25);base_api.finalize(terminal.b);fast_api.finalize(terminal.f);base_api.step(terminal.b,1);fast_api.step(terminal.f,1);compare(&terminal);destroy(&terminal);
 printf("{\"passed\":true,\"bit_identical_checkpoints\":%zu,\"compared_doubles\":%zu,\"iterations\":8193,\"large_actions\":257,\"growing_tree\":true,\"pending_without_growth\":true}\n",compared,checked_slots);
 return 0;
}
