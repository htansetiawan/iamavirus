/* A chance draw ONCE at the subgame root; descendants carry its result.
 * Mode0 is unrestricted, mode1 is fixed to the response model. */
#ifndef ASTRA_PERSISTENT_MODE_H
#define ASTRA_PERSISTENT_MODE_H
#include <assert.h>
#include <math.h>
static int persistent_count(double p) {
    assert(isfinite(p)&&p>=0&&p<=1);return p>0&&p<1?2:1;
}
static int persistent_mode(double p,int branch) {
    assert(branch>=0&&branch<persistent_count(p));return p==1?1:branch;
}
static double persistent_weight(double p,int mode) {
    assert(mode==0||mode==1);return mode?p:1-p;
}
#endif
