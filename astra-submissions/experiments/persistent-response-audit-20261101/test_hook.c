#include "gtcfr.c"

int main(int argc,char **argv) {
    assert(argc==3);fow_init();int kind=atoi(argv[2]);assert(kind>=0&&kind<=3);
    Tree t;memset(&t,0,sizeof(t));game_init(&t.g);t.persistent=kind>=2;t.model_prior=kind==3?1:.25;
    Position positions[2];float logw[2]={logf(.25),logf(.75)};
    for(int k=0;k<2;++k){pos_clear(&positions[k]);positions[k].side=WHITE;pos_put(&positions[k],0,WHITE,KING);pos_put(&positions[k],3,WHITE,ROOK);pos_put(&positions[k],63,BLACK,KING);pos_put(&positions[k],59,BLACK,ROOK);}
    pos_put(&positions[1],54,BLACK,PAWN);
    Belief b;memset(&b,0,sizeof(b));b.items=positions;b.logw=logw;b.count=2;b.us=WHITE;
    MoveList ours;ours.count=2;ours.moves[0]=MAKE_MOVE(3,11,NO_PIECE);ours.moves[1]=MAKE_MOVE(3,19,NO_PIECE);
    int modes=t.persistent?persistent_count(t.model_prior):1;
    int root=game_node(&t.g,NODE_CHANCE,0,-1,0),I=game_infoset(&t.g,0,2),world[4],indices[4],child[4][2];double shares[4];
    Position after=positions[0];Undo u;make_move(&after,ours.moves[0],&u);MoveList replies;generate_moves(&after,&replies);
    int J[2]={-1,-1},capture=-1;double fixed[256];
    for(int j=0;j<replies.count;++j){fixed[j]=1.0/replies.count;if(MOVE_FROM(replies.moves[j])==59&&MOVE_TO(replies.moves[j])==11)capture=j;}
    assert(capture>=0);
    for(int k=0;k<2;++k)for(int branch=0;branch<modes;++branch) {
        int n=k*modes+branch,mode=t.persistent?persistent_mode(t.model_prior,branch):0;
        world[n]=game_node(&t.g,NODE_PLAYER,0,I,0);indices[n]=k;
        shares[n]=(k?.75:.25)*(t.persistent?persistent_weight(t.model_prior,mode):1);
        child[n][0]=game_node(&t.g,NODE_TERMINAL,0,-1,k?-.2:.3);child[n][1]=game_node(&t.g,NODE_TERMINAL,0,-1,k?.8:.4);
        game_children(&t.g,world[n],child[n],NULL,2);
        if(k==0) {
            int kids[256];J[branch]=game_infoset(&t.g,1,replies.count);
            for(int j=0;j<replies.count;++j)kids[j]=game_node(&t.g,NODE_TERMINAL,0,-1,j==capture?-1:.5);
            game_expand_leaf(&t.g,child[n][0],1,J[branch],kids,replies.count);
        }
    }
    game_children(&t.g,root,world,shares,2*modes);game_finalize(&t.g);
    double *x=calloc(t.g.n_slots,sizeof(double));x[0]=.25;x[1]=.75;
    for(int branch=0;branch<modes;++branch) {
        int mode=t.persistent?persistent_mode(t.model_prior,branch):0;
        double c=t.persistent?(double)mode:(kind==1?.25:0);
        if(c>0)game_restrict(&t.g,J[branch],c,fixed);
        for(int a=0;a<replies.count;++a)x[t.g.is_offset[J[branch]]+a]=c*fixed[a]+(a==capture?1-c:0);
    }
    SearchResult result;memset(&result,0,sizeof(result));result.move=ours.moves[1];result.value=game_value(&t.g,x);
    assert(strcmp(getenv("ASTRA_BEST_REPLY_TRACE"),argv[1])==0);
    br_audit(&t,&b,indices,shares,2*modes,I,&ours,&result,x);
    free(x);game_free(&t.g);puts("full mode export passed");return 0;
}
