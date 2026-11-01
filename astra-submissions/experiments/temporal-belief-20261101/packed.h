#ifndef ASTRA_PACKED_RECENT_H
#define ASTRA_PACKED_RECENT_H
#include "../temporal-prior-20261101/inference.h"
#include <assert.h>

/* 16 move bits +3 type +4 captured-value +1 known +1 continued =25 bits. */
static uint32_t recent_pack(RecentOwn r) {
    if(!r.known)return 0;
    assert(r.type>=0 && r.type<6 && r.captured_value>=0 && r.captured_value<=9);
    return (uint32_t)r.move | ((uint32_t)r.type<<16) | ((uint32_t)r.captured_value<<19) |
           (1U<<23) | ((uint32_t)(r.continued!=0)<<24);
}
static RecentOwn recent_unpack(uint32_t bits) {
    RecentOwn r={0};r.known=(bits>>23)&1;
    if(r.known){r.move=(Move)(bits&65535);r.type=(bits>>16)&7;r.captured_value=(bits>>19)&15;r.continued=(bits>>24)&1;}
    return r;
}
static uint32_t recent_advance(uint32_t bits,const Position *p,Move m) {
    TemporalHistory h={0};h.side[p->side]=recent_unpack(bits);
    temporal_advance(&h,p,m);return recent_pack(h.side[p->side]);
}
static void recent_logits(uint32_t bits,const Position *p,const MoveList *moves,Move previous,int temporal,float *out) {
    TemporalHistory h={0};h.side[p->side]=recent_unpack(bits);
    temporal_logits(&h,p,moves,previous,temporal,out);
}
#endif
