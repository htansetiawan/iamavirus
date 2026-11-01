#include "proof.h"
#include "fow.h"
#include <stdlib.h>

int observable_fatal(const uint8_t tokens[64], const uint16_t *moves, int n,
                     uint8_t *fatal, uint8_t *witness) {
    if (!tokens || !moves || !fatal || !witness || n<1 || n>256) return 0;
    Position base;pos_clear(&base);base.side=WHITE;
    uint64_t unknown=0;
    for (int s=0;s<64;++s) {
        if (tokens[s]>13) return 0;
        if (tokens[s]<12) pos_put(&base,s,tokens[s]/6,tokens[s]%6);
        if (tokens[s]==12) unknown|=1ULL<<s;
    }
    if (king_square(&base,WHITE)<0) return 0;
    for (int a=0;a<n;++a) {
        int from=moves[a]&63,to=(moves[a]>>6)&63,promo=moves[a]>>12;
        if (promo>4 || tokens[from]>5) return 0;
        fatal[a]=0;witness[a]=64;
        if (tokens[to]==11) continue; /* king capture wins before own exposure */
        Position p=base;uint64_t fog=unknown;
        /* Legal diagonal pawn-to-empty is an en-passant action. Its captured
         * pawn square is known to be emptied by that permitted action. */
        if (tokens[from]==PAWN && (from%8!=to%8) && tokens[to]==13) {
            if (to<8) return 0;
            p.ep=to;fog&=~(1ULL<<(to-8));
        }
        Undo u;make_move(&p,MAKE_MOVE(from,to,promo ? promo : NO_PIECE),&u);
        fog&=~((1ULL<<from)|(1ULL<<to));
        if (u.rook_from>=0) fog&=~((1ULL<<u.rook_from)|(1ULL<<u.rook_to));
        int king=king_square(&p,WHITE);if (king<0) return 0;
        for (int s=0;s<64;++s) if (p.color[s]==BLACK && (attacks_from(&p,s)&(1ULL<<king))) {
            int type=p.piece[s],blocked=0;
            if (type==BISHOP || type==ROOK || type==QUEEN) {
                int dx=(king%8>s%8)-(king%8<s%8),dy=(king/8>s/8)-(king/8<s/8);
                for (int sq=s+dx+8*dy;sq!=king;sq+=dx+8*dy) if (fog&(1ULL<<sq)) {blocked=1;break;}
            }
            if (!blocked) {fatal[a]=1;witness[a]=(uint8_t)s;break;}
        }
    }
    return 1;
}
