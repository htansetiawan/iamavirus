#include "cfr.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>

/* Three actions, two worlds, five unequal-weight private-history copies.
 * Actions 0/1 look alike to the opponent; action 2 has a separate view. */
static void build(Game *g,int split,int initialized) {
 game_init(g);int root=game_node(g,NODE_CHANCE,0,-1,0),our=game_infoset(g,0,3);
 int world[5]={0,0,1,1,1};double probs[5]={.08,.32,.06,.18,.36};
 const double payoff[2][3][2]={{{.8,-.5},{-.4,.9},{.1,.2}},{{-.1,.7},{.9,-.8},{.3,.1}}};
 int infos[5][2];
 for(int k=0;k<(split?5:2);++k)for(int v=0;v<2;++v){infos[k][v]=game_infoset(g,1,2);if(initialized)game_start_on(g,infos[k][v],0);}
 int roots[5];
 for(int k=0;k<5;++k) {
  roots[k]=game_node(g,NODE_PLAYER,0,our,0);int actions[3];
  for(int a=0;a<3;++a) {
   actions[a]=game_node(g,NODE_PLAYER,1,infos[split?k:world[k]][a==2],0);int leaves[2];
   for(int b=0;b<2;++b)leaves[b]=game_node(g,NODE_TERMINAL,0,-1,payoff[world[k]][a][b]);
   game_children(g,actions[a],leaves,NULL,2);
  }
  game_children(g,roots[k],actions,NULL,3);
 }
 game_children(g,root,roots,probs,5);game_finalize(g);
}

/* A truly hidden private state: opponent cannot see which side is attacked.
 * Full two-state game value is 0; revealing our private state makes it -1. */
static double hiding(int coupled) {
 Game g;game_init(&g);int root=game_node(&g,NODE_CHANCE,0,-1,0);
 int info[2]={game_infoset(&g,1,2),-1};info[1]=coupled?info[0]:game_infoset(&g,1,2);
 int roots[2];double probabilities[2]={.5,.5};
 for(int hidden=0;hidden<2;++hidden) {
  roots[hidden]=game_node(&g,NODE_PLAYER,1,info[hidden],0);int kids[2];
  for(int block=0;block<2;++block)kids[block]=game_node(&g,NODE_TERMINAL,0,-1,block==hidden?-1:1);
  game_children(&g,roots[hidden],kids,NULL,2);
 }
 game_children(&g,root,roots,probabilities,2);game_finalize(&g);
 for(int t=1;t<=2048;++t)pcfr_iteration(&g,t);
 double x[4];pcfr_current(&g,x);double result=game_value(&g,x);game_free(&g);return result;
}

int main(void) {
 double error=0,value_error=0;
 for(int init=0;init<2;++init) {
  Game a,b;build(&a,0,init);build(&b,1,init);
  for(int t=1;t<=2048;++t) {
   pcfr_iteration(&a,t);pcfr_iteration(&b,t);double xa[32],xb[32];pcfr_current(&a,xa);pcfr_current(&b,xb);
   for(int k=0;k<3;++k)if(fabs(xa[k]-xb[k])>error)error=fabs(xa[k]-xb[k]);
   double e=fabs(game_value(&a,xa)-game_value(&b,xb));if(e>value_error)value_error=e;
  }
  game_free(&a);game_free(&b);
 }
 assert(error<1e-6&&value_error<1e-6);
 double hidden=hiding(1),revealed=hiding(0);assert(fabs(hidden)<1e-8&&fabs(revealed+1)<1e-8);
 printf("{\"passed\":true,\"iterations_per_initialization\":2048,\"initializations\":2,\"max_root_strategy_error\":%.17g,\"max_value_error\":%.17g,\"hidden_state_value\":%.17g,\"revealed_state_value\":%.17g}\n",error,value_error,hidden,revealed);
 return 0;
}
