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

static void fixture(int side, int K, const int *idx, const double *shares, double expected) {
    Tree t;memset(&t,0,sizeof(t));game_init(&t.g);t.us=side;t.root_loss=-2;
    Position positions[2];world(&positions[0],1);world(&positions[1],0);
    if(side==BLACK){flip(&positions[0]);flip(&positions[1]);}
    Belief b={0};b.items=positions;b.count=2;b.us=side;
    int mask=side==BLACK ? 56:0;
    MoveList ours;ours.count=2;ours.moves[0]=MAKE_MOVE(8^mask,16^mask,NO_PIECE);ours.moves[1]=MAKE_MOVE(4^mask,3^mask,NO_PIECE);
    double population[2]={.1,0};GtcfrParams params={0};
    params.root_loss_moves=ours.moves;params.root_loss_prob=population;params.root_loss_count=2;
    int root=game_node(&t.g,NODE_CHANCE,0,-1,0), I=game_infoset(&t.g,0,2);
    int worlds[2], kids[256], first_child[2];double before[2];uint64_t hist[2]={0,0};
    for(int k=0;k<K;++k) {
        worlds[k]=game_node(&t.g,NODE_TERMINAL,0,-1,0);
        int n=build_children(&t,&positions[idx[k]],hist,kids,&ours);assert(n==2);
        first_child[k]=kids[0];before[k]=t.g.nodes[kids[0]].value;
        game_expand_leaf(&t.g,worlds[k],0,I,kids,n);
    }
    game_children(&t.g,root,worlds,shares,K);
    root_loss_correct(&t,&b,&params,&ours,idx,shares,worlds,K);
    for(int k=0;k<K;++k) {
        assert(fabs(t.root_bias[first_child[k]]-expected)<1e-12);
        assert(fabs(t.g.nodes[first_child[k]].value-before[k]-expected)<1e-12);
    }
    game_finalize(&t.g);
    for(int k=0;k<K;++k) {
        int child=first_child[k];
        if(child<t.cap_leaf_of && t.leaf_of[child]>=0) {
            assert(expand_scored(&t,t.leaf_of[child],0,NULL,NULL));
            assert(t.g.nodes[child].type==NODE_PLAYER);
            assert(fabs(t.g.nodes[child].value-expected)<1e-12);
        }
    }
    game_grow(&t.g);
    double *strategy=malloc((size_t)t.g.n_slots*sizeof(double));pcfr_current(&t.g,strategy);
    double corrected_value=game_value(&t.g,strategy);
    for(int k=0;k<K;++k)t.g.nodes[first_child[k]].value-=expected;
    assert(fabs(corrected_value-game_value(&t.g,strategy)-.5*expected)<1e-12);
    free(strategy);cleanup(&t);
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
    const int only_safe[1]={1}; const double all[1]={1};
    const int distinct[2]={0,1}; const double repeated[2]={.25,.75};
    const double enumeration[2]={.1,.9};
    for(int side=WHITE;side<=BLACK;++side){
        fixture(side,1,only_safe,all,-.2);
        fixture(side,2,distinct,repeated,.3);
        fixture(side,2,distinct,enumeration,0);
    }
    puts("root CV: both colours, sharp weighting, event precedence, illegal fallback, merged shares, subtraction, full enumeration and growth passed");
    return 0;
}
