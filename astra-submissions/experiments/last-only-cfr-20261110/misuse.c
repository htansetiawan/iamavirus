#include "cfr.h"
int main(void){Game g;game_init(&g);game_node(&g,NODE_TERMINAL,0,-1,0);game_finalize(&g);double out=0;pcfr_average(&g,&out);game_free(&g);return 0;}
