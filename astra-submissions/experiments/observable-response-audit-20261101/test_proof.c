#include "proof.h"
#include "fow.h"
#include <assert.h>
#include <string.h>

static int test(uint8_t *t,int from,int to,int promo) {
    uint16_t move=(uint16_t)(from|(to<<6)|(promo<<12));uint8_t f,w;
    assert(observable_fatal(t,&move,1,&f,&w));return f;
}
int main(void) {
    fow_init();uint8_t t[64];memset(t,13,64);
    t[4]=KING;t[0]=ROOK;t[60]=6+ROOK;
    assert(test(t,0,8,0)==1); /* known clear file */
    t[28]=12;assert(test(t,0,8,0)==0); /* unknown blocker prevents proof */
    t[28]=PAWN;assert(test(t,0,8,0)==0); /* known own screen */
    assert(test(t,28,36,0)==0); /* screen remains on file */
    t[37]=6+PAWN;assert(test(t,28,37,0)==1); /* capture vacates screen */
    memset(t,12,64);t[4]=KING;t[0]=ROOK;t[21]=6+KNIGHT;t[8]=13;
    assert(test(t,0,8,0)==1); /* knight proof ignores intervening fog */
    t[21]=13;t[11]=6+PAWN;assert(test(t,0,8,0)==1);
    t[11]=13;t[12]=6+KING;assert(test(t,0,8,0)==1);
    assert(test(t,4,12,0)==0); /* capture enemy king wins */
    memset(t,13,64);t[4]=KING;t[7]=ROOK;t[62]=6+ROOK;
    assert(test(t,4,6,0)==1); /* castled king under known rook */
    t[38]=12;assert(test(t,4,6,0)==0); /* dark rook line not proven */
    memset(t,13,64);t[39]=KING;t[36]=PAWN;t[35]=6+PAWN;t[32]=6+ROOK;
    assert(test(t,36,43,0)==1); /* en passant removes both rank screens */
    memset(t,13,64);t[4]=KING;t[48]=PAWN;t[60]=6+ROOK;
    for(int p=1;p<=4;++p)assert(test(t,48,56,p)==1);
    return 0;
}
