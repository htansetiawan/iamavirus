#include <assert.h>
#include "gtcfr.c"

#ifdef HAS_MODE
static void mode_fixture(void) {
    visible_config();assert(visible_weights);
    Tree t;memset(&t,0,sizeof(t));game_init(&t.g);t.us=WHITE;t.persistent=1;t.model_prior=.25;
    Position p;pos_start(&p);p.side=BLACK;uint64_t hist[2]={123,456};
    int root=game_node(&t.g,NODE_CHANCE,0,-1,0),nodes[2],leaves[2];double mass[2]={.75,.25};
    for(int mode=0;mode<2;++mode){nodes[mode]=game_node(&t.g,NODE_TERMINAL,0,-1,0);remember_leaf(&t,nodes[mode],&p,hist,mode);leaves[mode]=t.leaf_of[nodes[mode]];}
    game_children(&t.g,root,nodes,mass,2);
    for(int depth=0;depth<3;++depth) {
        int ids[2],next[2]={-1,-1};
        for(int mode=0;mode<2;++mode) {
            Leaf prior=t.leaves[leaves[mode]];int before=t.n_leaves;assert(prior.opponent_mode==mode);
            assert(expand(&t,leaves[mode])==1);
            for(int j=before;j<t.n_leaves;++j)assert(t.leaves[j].opponent_mode==mode);
            const GameNode *n=&t.g.nodes[prior.node];ids[mode]=n->infoset;
            assert(n->player==(depth%2==0?1:0));assert(t.g.confidence[n->infoset]==(n->player==1&&mode==1?1:0));
            for(int a=0;a<n->count;++a){int child=t.g.child[n->first+a];if(t.leaf_of[child]>=0){next[mode]=t.leaf_of[child];break;}}
            assert(next[mode]>=0);
        }
        if(depth%2==0){assert(ids[0]!=ids[1]);assert(t.g.confidence[ids[0]]==0&&t.g.confidence[ids[1]]==1);}else assert(ids[0]==ids[1]);
        assert(t.leaves[next[0]].hist[0]==t.leaves[next[1]].hist[0]);assert(t.leaves[next[0]].hist[1]==t.leaves[next[1]].hist[1]);
        char b0[65],b1[65];pos_to_board_string(&t.leaves[next[0]].pos,b0);pos_to_board_string(&t.leaves[next[1]].pos,b1);assert(strcmp(b0,b1)==0);
        leaves[0]=next[0];leaves[1]=next[1];
    }
    assert(t.response_calls==2 && t.response_failures==0 && t.response_mismatches==0);
    assert(t.mode_expansions[0]==3&&t.mode_expansions[1]==3);
    game_finalize(&t.g);for(int i=1;i<=20;++i)pcfr_iteration(&t.g,i);
    printf("{\"mode_propagation_depth\":3,\"own_infosets_shared\":true,\"opponent_infosets_separate\":true,\"model_calls\":%lu}\n",t.response_calls);
    game_free(&t.g);free(t.leaves);free(t.leaf_of);free(t.keys);free(t.vals);free(t.response_keys);free(t.visits);
}
#endif

int main(int argc,char **argv) {
    fow_init();zobrist_init();
#ifdef HAS_MODE
    if(argc>1&&strcmp(argv[1],"fixture")==0){mode_fixture();free(visible_weights);return 0;}
#endif
    Belief b;belief_init_start(&b,WHITE,1000);GtcfrParams params;memset(&params,0,sizeof(params));
    params.samples=32;params.max_nodes=20000;params.seed=2141101;params.king_risk=2;
    SearchResult result;assert(gtcfr_decide(&b,&params,&result));char move[6];move_to_uci(result.move,move);
    printf("{\"move\":\"%s\",\"value\":%.17g,\"probability\":%.17g,\"samples\":%d,\"moves\":%d,\"infosets\":%d,\"nodes\":%d,\"iterations\":%d}\n",move,result.value,result.probability,result.samples,result.our_moves,result.opponent_infosets,result.nodes,result.iterations);
    belief_free(&b);free(visible_weights);return 0;
}
