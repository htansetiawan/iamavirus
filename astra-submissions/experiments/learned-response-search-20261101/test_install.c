#include <assert.h>
#include "gtcfr.c"

int main(int argc, char **argv) {
    assert(argc == 3);
    setenv("ASTRA_VISIBLE_CONFIDENCE", argv[2], 1);
    setenv("ASTRA_VISIBLE_MODEL", argv[1], 1);
    fow_init();
    Tree t; memset(&t, 0, sizeof(t)); game_init(&t.g);
    Leaf leaf; memset(&leaf, 0, sizeof(leaf)); pos_start(&leaf.pos); leaf.pos.side=BLACK;
    MoveList moves; generate_moves(&leaf.pos,&moves);
    int I=game_infoset(&t.g,1,moves.count);
    dbr_install(&t,I,&leaf);
    if (atof(argv[2])==0 || strcmp(argv[1],"missing")==0) {
        assert(t.g.confidence[I]==0 && t.response_calls==0 && !t.response_keys);
        assert(visible_load_failed==(strcmp(argv[1],"missing")==0));
        game_free(&t.g); return 0;
    }
    assert(t.g.confidence[I]==.25 && t.response_calls==1 && t.response_failures==0);
    double q[256]; memcpy(q,t.g.fixed_policy+t.g.is_offset[I],moves.count*sizeof(double));
    /* Different hidden white placement, identical black view/legal actions. */
    char before[65],after[65]; observation(&leaf.pos,BLACK,before);
    pos_remove(&leaf.pos,1);pos_put(&leaf.pos,16,WHITE,KNIGHT);
    observation(&leaf.pos,BLACK,after);assert(strcmp(before,after)==0);
    dbr_install(&t,I,&leaf);
    assert(t.response_calls==1 && t.response_reuses==1 && t.response_mismatches==0);
    assert(memcmp(q,t.g.fixed_policy+t.g.is_offset[I],moves.count*sizeof(double))==0);
    int ours=game_infoset(&t.g,0,moves.count);dbr_install(&t,ours,&leaf);
    assert(t.g.confidence[ours]==0 && t.response_calls==1);
    for (int k=0;k<300;++k) {
        int J=game_infoset(&t.g,1,moves.count);dbr_install(&t,J,&leaf);
        assert(t.g.confidence[J]==.25);
    }
    assert(t.response_calls==301 && t.response_key_cap>300);
    /* A conflicting observable key disables the restriction and reports it. */
    t.response_keys[I]^=2;dbr_install(&t,I,&leaf);
    assert(t.g.confidence[I]==0 && t.response_mismatches==1);
    game_free(&t.g);free(t.response_keys);free(visible_weights);visible_weights=NULL;
    return 0;
}
