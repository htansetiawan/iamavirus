#include "gtcfr.c"

int main(int argc,char **argv) {
    assert(argc==2 && strcmp(getenv("ASTRA_RESPONSE_TRACE"),argv[1])==0);fow_init();
    Tree t;memset(&t,0,sizeof(t));game_init(&t.g);
    Position positions[2];float logw[2]={logf(.25),logf(.75)};
    for(int k=0;k<2;++k){pos_clear(&positions[k]);positions[k].side=WHITE;pos_put(&positions[k],0,WHITE,KING);pos_put(&positions[k],3,WHITE,ROOK);pos_put(&positions[k],63,BLACK,KING);pos_put(&positions[k],59,BLACK,ROOK);}
    pos_put(&positions[1],54,BLACK,PAWN);
    Belief b;memset(&b,0,sizeof(b));b.items=positions;b.logw=logw;b.count=2;b.us=WHITE;
    MoveList ours;ours.count=2;ours.moves[0]=MAKE_MOVE(3,11,NO_PIECE);ours.moves[1]=MAKE_MOVE(3,19,NO_PIECE);
    int root=game_node(&t.g,NODE_CHANCE,0,-1,0),I=game_infoset(&t.g,0,2),world[2],child[2][2];
    double shares[2]={.25,.75};int indices[2]={0,1};
    for(int k=0;k<2;++k){world[k]=game_node(&t.g,NODE_PLAYER,0,I,0);child[k][0]=game_node(&t.g,NODE_TERMINAL,0,-1,k?-.2:.3);child[k][1]=game_node(&t.g,NODE_TERMINAL,0,-1,k?.8:.4);game_children(&t.g,world[k],child[k],NULL,2);}
    game_children(&t.g,root,world,shares,2);double *initial=trace_initial(&t.g,2);
    Position after=positions[0];Undo u;make_move(&after,ours.moves[0],&u);MoveList replies;generate_moves(&after,&replies);
    int J=game_infoset(&t.g,1,replies.count),kids[256],capture=-1;double fixed[256];
    for(int j=0;j<replies.count;++j){int takes=MOVE_FROM(replies.moves[j])==59 && MOVE_TO(replies.moves[j])==11;if(takes)capture=j;kids[j]=game_node(&t.g,NODE_TERMINAL,0,-1,takes?-1:.5);fixed[j]=1.0/replies.count;}
    assert(capture>=0);game_expand_leaf(&t.g,child[0][0],1,J,kids,replies.count);game_finalize(&t.g);if(getenv("FIXTURE_RESTRICT"))game_restrict(&t.g,J,.25,fixed);
    double *x=calloc(t.g.n_slots,sizeof(double));x[0]=.25;x[1]=.75;
    for(int j=0;j<replies.count;++j)x[t.g.is_offset[J]+j]=.25/replies.count+(j==capture?.75:0);
    double q0=.25*(-.625-.375/replies.count)+.75*(-.2),q1=.25*.4+.75*.8;
    SearchResult result;memset(&result,0,sizeof(result));result.move=ours.moves[1];result.value=.25*q0+.75*q1;
    trace_final(&t,&b,indices,shares,2,I,&ours,&result,x,initial);free(x);game_free(&t.g);
    return 0;
}
