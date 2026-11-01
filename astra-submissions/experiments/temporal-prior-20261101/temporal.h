#ifndef ASTRA_TEMPORAL_H
#define ASTRA_TEMPORAL_H
#include "native/movemodel.h"
#include <string.h>

enum { TP_FEATURES = 52 };
typedef struct { Move move; int known, type, captured_value, continued; } RecentOwn;
typedef struct { RecentOwn side[2]; } TemporalHistory;

static int temporal_capture_value(const Position *p, Move m) {
    static const int value[7] = {1,3,3,5,9,0,0};
    int from=MOVE_FROM(m), to=MOVE_TO(m), captured=p->piece[to];
    if (p->piece[from]==PAWN && to==p->ep && captured==NO_PIECE) captured=PAWN;
    return value[captured];
}

/* Called BEFORE advancing p, AFTER extracting features for the chosen action. */
static void temporal_advance(TemporalHistory *h, const Position *p, Move m) {
    RecentOwn *r=&h->side[p->side];
    const int type=p->piece[MOVE_FROM(m)];
    const int same=r->known && MOVE_FROM(m)==MOVE_TO(r->move) && type==r->type;
    r->captured_value=temporal_capture_value(p,m);
    r->continued=same;
    r->type=MOVE_PROMO(m)==NO_PIECE ? type : MOVE_PROMO(m);
    r->move=m; r->known=1;
}

static void temporal_features(const TemporalHistory *h, const Position *p, Move m,
                              float out[TP_FEATURES]) {
    memset(out,0,TP_FEATURES*sizeof(float));
    const RecentOwn *r=&h->side[p->side];
    if (!r->known) return;
    const int type=p->piece[MOVE_FROM(m)];
    out[r->type*6+type]=1;
    const int same=MOVE_FROM(m)==MOVE_TO(r->move) && type==r->type;
    if (!same) return;
    out[36+type]=1;
    if (r->captured_value) out[42+type]=1;
    out[48]=MOVE_TO(m)==MOVE_FROM(r->move);
    out[49]=(float)r->continued;
    out[50]=r->captured_value>0 && temporal_capture_value(p,m)>0;
    out[51]=(float)r->captured_value/9.0f;
}
#endif
