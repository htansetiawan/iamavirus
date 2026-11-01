#include <assert.h>
#include <math.h>
#include <stdio.h>
/* Test the actual private builder, guard cache, and leaf-growth implementation. */
#define main frontend_not_invoked
#include "../src/main.c"
#undef main
#include "../src/gtcfr.c"

static void world(Position *p, int dangerous) {
    pos_clear(p);p->side=WHITE;
    pos_put(p,4,WHITE,KING); pos_put(p,8,WHITE,PAWN);
    pos_put(p,63,BLACK,KING); pos_put(p,dangerous ? 60 : 56,BLACK,ROOK);
}

static void cleanup(Tree *t) {
    free(t->leaves);free(t->leaf_of);free(t->keys);free(t->vals);free(t->visits);free(t->root_bias);game_free(&t->g);
}

static void flip(Position *p) {
    Position q;pos_clear(&q);q.side=p->side^1;
    for(int sq=0;sq<64;++sq)
        if(p->piece[sq]!=NO_PIECE)pos_put(&q,sq^56,p->color[sq]^1,p->piece[sq]);
    *p=q;
}

/* Independent oracle: push a prescribed affine payoff transform into every
 * terminal of an unmodified tree. Compare to the lazy growth implementation. */
static void transform_terminals(Game *g, int node, double scale, double bias) {
    GameNode *n=&g->nodes[node];
    if(n->type==NODE_TERMINAL) { n->value=scale*n->value+bias;return; }
    assert(n->value==0);
    for(int a=0;a<n->count;++a)transform_terminals(g,g->child[n->first+a],scale,bias);
}

static void fixture(int side, int mode, int K, const int *idx, const double *shares, double population) {
    Tree t={0},raw={0};game_init(&t.g);game_init(&raw.g);
    t.us=raw.us=side;t.root_loss=raw.root_loss=-2;
    Position positions[2];world(&positions[0],1);world(&positions[1],0);
    if(side==BLACK){flip(&positions[0]);flip(&positions[1]);}
    Belief b={0};b.items=positions;b.count=2;b.us=side;
    int mask=side==BLACK ? 56:0;
    MoveList ours;ours.count=2;ours.moves[0]=MAKE_MOVE(8^mask,16^mask,NO_PIECE);ours.moves[1]=MAKE_MOVE(4^mask,3^mask,NO_PIECE);
    double risks[2]={population,0};GtcfrParams params={0};
    params.root_loss_moves=ours.moves;params.root_loss_prob=risks;params.root_loss_count=2;params.root_loss_mode=mode;
    int root=game_node(&t.g,NODE_CHANCE,0,-1,0), I=game_infoset(&t.g,0,2);
    assert(game_node(&raw.g,NODE_CHANCE,0,-1,0)==root);assert(game_infoset(&raw.g,0,2)==I);
    int worlds[2],kids[256],rkids[256];uint64_t hist[2]={0,0};
    for(int k=0;k<K;++k) {
        worlds[k]=game_node(&t.g,NODE_TERMINAL,0,-1,0);
        assert(game_node(&raw.g,NODE_TERMINAL,0,-1,0)==worlds[k]);
        int n=build_children(&t,&positions[idx[k]],hist,kids,&ours);assert(n==2);
        assert(build_children(&raw,&positions[idx[k]],hist,rkids,&ours)==n);
        assert(memcmp(kids,rkids,(size_t)n*sizeof(int))==0);
        game_expand_leaf(&t.g,worlds[k],0,I,kids,n);game_expand_leaf(&raw.g,worlds[k],0,I,rkids,n);
    }
    game_children(&t.g,root,worlds,shares,K);game_children(&raw.g,root,worlds,shares,K);
    root_loss_correct(&t,&b,&params,&ours,idx,shares,worlds,K);
    game_finalize(&t.g);game_finalize(&raw.g);
    /* Grow each initial frontier, then one of its frontiers. Includes both
     * players' moves, terminal wins/losses and nonterminal descendants. */
    int initial=t.n_leaves;
    for(int i=0;i<initial;++i) {
        assert(t.leaves[i].node==raw.leaves[i].node);
        int next=t.n_leaves;
        assert(expand_scored(&t,i,0,NULL,NULL)==expand_scored(&raw,i,0,NULL,NULL));
        if(t.n_leaves>next)
            assert(expand_scored(&t,next,0,NULL,NULL)==expand_scored(&raw,next,0,NULL,NULL));
    }
    for(int a=0;a<ours.count;++a) {
        double loss=0,safe=0;
        for(int k=0;k<K;++k) {
            if(root_loss_event(&positions[idx[k]],ours.moves[a]))loss+=shares[k];else safe+=shares[k];
        }
        double q=astra_calibrated_king_loss(risks[a]);
        for(int k=0;k<K;++k) {
            int child=raw.g.child[raw.g.nodes[worlds[k]].first+a];
            int fatal=root_loss_event(&positions[idx[k]],ours.moves[a]);
            double scale=1,bias=0;
            if(mode==1 && safe>0) {
                if(fatal)scale=q/loss;
                else scale=(1-q)/safe;
                if(loss==0)bias=-2*q;
            } else if(mode==2)bias=-2*(q-loss);
            transform_terminals(&raw.g,child,scale,bias);
        }
    }
    game_grow(&t.g);game_grow(&raw.g);
    assert(t.g.n_slots==raw.g.n_slots);
    double *x=malloc((size_t)t.g.n_slots*sizeof(double)),*y=malloc((size_t)t.g.n_slots*sizeof(double));
    pcfr_current(&t.g,x);pcfr_current(&raw.g,y);
    assert(fabs(game_value(&t.g,x)-game_value(&raw.g,y))<1e-10);
    for(int player=0;player<2;++player)
        assert(fabs(best_response_value(&t.g,x,player)-best_response_value(&raw.g,y,player))<1e-9);
    for(int iter=1;iter<=300;++iter) {
        pcfr_iteration(&t.g,iter);pcfr_iteration(&raw.g,iter);
        for(int j=0;j<t.g.n_slots;++j)assert(fabs(t.g.regret[j]-raw.g.regret[j])<1e-7);
    }
    pcfr_current(&t.g,x);pcfr_current(&raw.g,y);
    for(int j=0;j<t.g.n_slots;++j)assert(fabs(x[j]-y[j])<1e-6);
    assert(fabs(game_value(&t.g,x)-game_value(&raw.g,y))<1e-7);
    free(x);free(y);cleanup(&t);cleanup(&raw);
}

static void guard_events(void) {
    Position p[2];world(&p[0],1);world(&p[1],0);
    Belief b={0};b.items=p;b.count=2;
    const Move pawn=MAKE_MOVE(8,16,NO_PIECE);
    double a,sharp,cv;king_risks(&b,pawn,20000,2,&a,&sharp,&cv);
    assert(fabs(a-.5)<1e-12 && fabs(sharp-.5)<1e-12 && fabs(cv-.5)<1e-12);
    assert(root_loss_event(&p[0],pawn) && !root_loss_event(&p[1],pawn));
    /* Search draws use exp(logw), not the flatter guard weighting. */
    float weights[2]={(float)log(.25),0};b.logw=weights;
    king_risks(&b,pawn,20000,2,&a,&sharp,&cv);
    assert(fabs(a-1.0/3)<2e-8 && fabs(sharp-.2)<2e-8 && fabs(cv-.2)<2e-8);
    b.logw=NULL;
    /* Capturing the opposing king wins before testing our own exposure. */
    pos_remove(&p[0],63);pos_put(&p[0],12,BLACK,KING);b.count=1;
    const Move capture=MAKE_MOVE(4,12,NO_PIECE);
    king_risks(&b,capture,20000,2,&a,&sharp,&cv);
    assert(sharp==1 && cv==0 && !root_loss_event(&p[0],capture));
    /* A castling-shaped move without rights is illegal in this world. */
    const Move illegal=MAKE_MOVE(4,2,NO_PIECE);
    assert(!root_loss_event(&p[0],illegal));
    king_risks(&b,illegal,20000,2,&a,&sharp,&cv);assert(cv==0);
}

int main(void) {
    fow_init();zobrist_init();guard_events();
    const int only_safe[1]={1},only_lost[1]={0}; const double all[1]={1};
    const int distinct[2]={0,1}; const double repeated[2]={.25,.75};
    const double tiny_safe[2]={1-1e-10,1e-10};
    for(int side=WHITE;side<=BLACK;++side)for(int mode=0;mode<=2;++mode){
        fixture(side,mode,1,only_safe,all,.1);
        fixture(side,mode,1,only_lost,all,.1);
        fixture(side,mode,2,distinct,repeated,.1);
        fixture(side,mode,2,distinct,repeated,0);
        fixture(side,mode,2,distinct,repeated,1);
        fixture(side,mode,2,distinct,tiny_safe,.1);
    }
    puts("calibrated root: both colours, modes off/mixture/residual, zero/all/partial loss samples, tiny survival, endpoint calibration, two growth levels, both best responses and 300 CFR iterations match explicit terminal-payoff oracle");
    return 0;
}
