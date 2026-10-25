/* Analytic counterexamples and target-oracle checks against the immutable v35 C. */
#include "teacher_targets.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void close_to(double got, double want) { assert(fabs(got-want) < 1e-10); }
static int terminal(Game *g, double v) { return game_node(g,NODE_TERMINAL,0,-1,v); }

int main(void) {
    Game g; game_init(&g);
    int R = game_infoset(&g,0,2), I = game_infoset(&g,0,2);
    int root = game_node(&g,NODE_PLAYER,0,R,0);
    int next = game_node(&g,NODE_PLAYER,0,I,0);
    int children[2] = {terminal(&g,0),terminal(&g,0)};
    game_children(&g,next,children,NULL,2);
    int rc[2] = {next,terminal(&g,0)};
    game_children(&g,root,rc,NULL,2); game_finalize(&g);
    double x[4], avg[4], corrected[4] = {0};
    for (int iteration=1; iteration<=2; ++iteration) {
        double p = iteration==1 ? .9 : .1;
        g.regret[0]=g.regret[2]=p; g.regret[1]=g.regret[3]=1-p;
        memset(g.last,0,4*sizeof(double)); pcfr_current(&g,x);
        TeacherTargets t = teacher_targets(&g,x);
        assert(t.recall_ok); close_to(t.own_reach[I],p);
        close_to(t.cf_mass[I],1); /* own reach must not enter CF mass */
        for (int j=0;j<g.n_infosets;++j)
            for (int a=0;a<2;++a)
                corrected[2*j+a] += iteration*t.own_reach[j]*x[2*j+a];
        teacher_targets_free(&t); pcfr_iteration(&g,iteration);
    }
    pcfr_average(&g,avg);
    double proper_child = corrected[2]/(corrected[2]+corrected[3]);
    close_to(avg[0],11.0/30); close_to(avg[2],11.0/30);
    close_to(proper_child,83.0/110);
    close_to(avg[0]*proper_child,83.0/300);
    printf("{\"archive_child_average\":%.12f,\"realization_weighted_child_average\":%.12f,"
           "\"archive_enter_A_probability\":%.12f,\"correct_enter_A_probability\":%.12f,",
           avg[2],proper_child,avg[0]*avg[2],avg[0]*proper_child);
    game_free(&g);

    /* Chance .25/.75, then P0 Enter=.2, then one shared P1 infoset A=.4.
       P1's A/B utilities: (1,-1) in world 0; (-1,1) in world 1.
       CF mass is .2; CF Q=(-.1,.1), normalised Q=(-.5,.5).
       P1 own reach is 1, not two (the number of represented histories). */
    game_init(&g); int E=game_infoset(&g,0,2), J=game_infoset(&g,1,2);
    int chance=game_node(&g,NODE_CHANCE,0,-1,0), worlds[2];
    for (int k=0;k<2;++k) {
        worlds[k]=game_node(&g,NODE_PLAYER,0,E,0);
        int opponent=game_node(&g,NODE_PLAYER,1,J,0);
        double v=k==0 ? -1 : 1;
        int replies[2]={terminal(&g,v),terminal(&g,-v)};
        game_children(&g,opponent,replies,NULL,2);
        int choices[2]={opponent,terminal(&g,0)};
        game_children(&g,worlds[k],choices,NULL,2);
    }
    double probabilities[2]={.25,.75};
    game_children(&g,chance,worlds,probabilities,2); game_finalize(&g);
    double policy[4]={.2,.8,.4,.6};
    TeacherTargets t=teacher_targets(&g,policy);
    assert(t.recall_ok && t.histories[J]==2);
    close_to(t.cf_mass[J],.2); close_to(t.own_reach[J],1);
    close_to(t.cf_q[2],-.1); close_to(t.cf_q[3],.1);
    close_to(t.root_value,-.02); close_to(t.root_value,game_value(&g,policy));
    for(int a=0;a<4;++a) close_to(g.regret[a],0); /* read-only */
    teacher_targets_free(&t);
    policy[0]=0; policy[1]=1;
    t=teacher_targets(&g,policy);
    close_to(t.cf_mass[J],0); close_to(t.cf_q[2],0);
    teacher_targets_free(&t); game_free(&g);
    printf("\"counterfactual_target_checks\":\"passed\",\"deployment_uses_average\":false}\n");
    return 0;
}
