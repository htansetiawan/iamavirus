#ifndef ASTRA_RESPONSE_PROJECTION_H
#define ASTRA_RESPONSE_PROJECTION_H
/* Minimal KL(q_new || q_old) projection onto zero mass on proven losses.
 * All-proven or zero surviving mass: preserve the original distribution.
 * This modifies only the fixed learned component, not legal/free actions. */
static int project_response(double *q, const uint8_t *fatal, int n, double *mass) {
    int removed=0;double safe=0;*mass=0;
    for(int a=0;a<n;++a) {
        if(fatal[a]) {++removed;*mass+=q[a];} else safe+=q[a];
    }
    if(!removed) return 0;
    if(removed==n || !(safe>0)) return -1;
    for(int a=0;a<n;++a) q[a]=fatal[a] ? 0 : q[a]/safe;
    return removed;
}
#endif
