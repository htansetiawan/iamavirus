#include "expansion_values.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
Game *fixture(int seed, int invalid);
Game *wide_fixture(void);
void grow_fixture(Game *g);
void drop_fixture(Game *g);

int main(void) {
    for (int trial=0; trial<20; ++trial) {
        Game *g=fixture(trial,trial%2);ExpansionValues v={0};
        for (int it=1; it<=100; ++it) {
            if(it==50)grow_fixture(g);
            pcfr_iteration(g,it);
            double *x=malloc((size_t)g->n_slots*sizeof(double));pcfr_current(g,x);
            expansion_values_refresh(&v,g,x);assert(isfinite(v.root_value));free(x);
        }
        expansion_values_free(&v);drop_fixture(g);
    }
    Game *g=wide_fixture();ExpansionValues v={0};double x[257];
    for(int a=0;a<257;++a)x[a]=1.0/257;
    expansion_values_refresh(&v,g,x);assert(expansion_values_available(&v,0,0,257));
    expansion_values_free(&v);drop_fixture(g);
    puts("2000 dynamic-tree observations and 257-action fixture passed");return 0;
}
