#include <assert.h>
#include "gtcfr.c"

int main(int argc,char **argv) {
    assert(argc==3);setenv("ASTRA_VISIBLE_MODEL",argv[1],1);
    setenv("ASTRA_VISIBLE_CONFIDENCE",".25",1);setenv("ASTRA_VISIBLE_PROJECT",argv[2],1);
    fow_init();Tree t;memset(&t,0,sizeof(t));game_init(&t.g);
    Leaf leaf;memset(&leaf,0,sizeof(leaf));pos_clear(&leaf.pos);leaf.pos.side=BLACK;
    /* Black sees Nf6 through pawn g7; moving Ra8 leaves its king in a known
     * knight attack. Pawn captures/king escapes remain valid alternatives. */
    pos_put(&leaf.pos,60,BLACK,KING);pos_put(&leaf.pos,54,BLACK,PAWN);
    pos_put(&leaf.pos,56,BLACK,ROOK);pos_put(&leaf.pos,45,WHITE,KNIGHT);pos_put(&leaf.pos,0,WHITE,KING);
    MoveList moves;generate_moves(&leaf.pos,&moves);char view[65];observation(&leaf.pos,BLACK,view);
    uint8_t tokens[64],fatal[256],witness[256];uint16_t encoded[256];double raw[256];
    assert(visible_pack(view,BLACK,moves.moves,moves.count,tokens,encoded));visible_config();
    assert(astra_response_probs(visible_weights,tokens,encoded,moves.count,raw));
    assert(observable_fatal(tokens,encoded,moves.count,fatal,witness));
    int nbad=0;double safe=0;
    for(int a=0;a<moves.count;++a){nbad+=fatal[a];if(!fatal[a])safe+=raw[a];}
    assert(nbad>0 && nbad<moves.count && safe>0 && safe<1);
    int I=game_infoset(&t.g,1,moves.count);dbr_install(&t,I,&leaf);
    assert(t.g.confidence[I]==.25 && t.response_failures==0);
    for(int a=0;a<moves.count;++a) {
        double expected=atoi(argv[2])==1 ? (fatal[a] ? 0 : raw[a]/safe) : raw[a];
        assert(fabs(t.g.fixed_policy[t.g.is_offset[I]+a]-expected)<1e-13);
    }
    assert(t.response_projected_sets==(unsigned)(atoi(argv[2])==1));
    dbr_install(&t,I,&leaf);assert(t.response_calls==1 && t.response_reuses==1 && t.response_mismatches==0);
    double q[3]={.2,.3,.5},mass;uint8_t all[3]={1,1,1},none[3]={0,0,0};
    assert(project_response(q,all,3,&mass)==-1 && fabs(mass-1)<1e-15 && q[0]==.2 && q[1]==.3 && q[2]==.5);
    assert(project_response(q,none,3,&mass)==0 && mass==0 && q[0]==.2);
    /* Includes zero-probability surviving actions without division by zero. */
    double zero[2]={1,0};uint8_t one[2]={1,0};assert(project_response(zero,one,2,&mass)==-1 && zero[0]==1);
    game_free(&t.g);free(t.response_keys);free(visible_weights);visible_weights=NULL;
    return 0;
}
