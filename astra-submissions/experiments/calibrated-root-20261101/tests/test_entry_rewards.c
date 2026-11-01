#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../src/cfr.h"

/* Equivalent imperfect-information games: the reward is either paid on entry
 * to a subtree or pushed into every terminal below it. Exercise both players,
 * chance weighting, regrets, value, and best response against the same policy. */
static void build(Game *g, int entry) {
    game_init(g);
    int I = game_infoset(g, 0, 2), J[2] = {game_infoset(g,1,2), game_infoset(g,1,2)};
    int root = game_node(g,NODE_CHANCE,0,-1,entry ? .1 : 0);
    const double reward[2] = {-.08,.06};
    const double u[2][2][2] = {{{.6,-.5},{.2,.4}},{{-.2,.1},{-.7,.9}}};
    int worlds[2]; double p[2] = {.3,.7};
    for (int w=0;w<2;++w) {
        worlds[w] = game_node(g,NODE_PLAYER,0,I,0);
        int actions[2];
        for (int a=0;a<2;++a) {
            actions[a] = game_node(g,NODE_PLAYER,1,J[a],entry ? reward[a] : 0);
            int leaves[2];
            for (int b=0;b<2;++b) leaves[b]=game_node(g,NODE_TERMINAL,0,-1,u[w][a][b]+(entry ? 0 : reward[a]+.1));
            game_children(g,actions[a],leaves,NULL,2);
        }
        game_children(g,worlds[w],actions,NULL,2);
    }
    game_children(g,root,worlds,p,2); game_finalize(g);
}

int main(void) {
    Game a,b; build(&a,1); build(&b,0); double x[6],y[6];
    for (int i=0;i<6;++i) x[i]=.5;
    assert(fabs(game_value(&a,x)-game_value(&b,x))<1e-12);
    for (int p=0;p<2;++p) assert(fabs(best_response_value(&a,x,p)-best_response_value(&b,x,p))<1e-12);
    assert(fabs(exploitability(&a,x)-exploitability(&b,x))<1e-12);
    for (int t=1;t<=500;++t) {
        pcfr_iteration(&a,t); pcfr_iteration(&b,t);
        for (int i=0;i<6;++i) assert(fabs(a.regret[i]-b.regret[i])<1e-8);
    }
    pcfr_current(&a,x); pcfr_current(&b,y);
    for (int i=0;i<6;++i) assert(fabs(x[i]-y[i])<1e-7);
    assert(fabs(game_value(&a,x)-game_value(&b,y))<1e-7);
    game_free(&a);game_free(&b);
    puts("entry rewards: value, both best responses, exploitability and 500 CFR iterations equivalent");
    return 0;
}
