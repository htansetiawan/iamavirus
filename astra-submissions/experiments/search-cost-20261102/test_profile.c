#include "profile.h"
int main(void) {
    /* Disabled calls are harmless; nested calls in the same bucket must not
       double-count. Test clock: root=9, SF=3, solver=2, strategy=1, other=3. */
    prof_leave(prof_enter(PROF_SF));
    prof_begin(); int root=prof_enter(PROF_OTHER);
    int a=prof_enter(PROF_SF), b=prof_enter(PROF_SF);
    prof_leave(b); prof_leave(a);
    a=prof_enter(PROF_SOLVE); b=prof_enter(PROF_STRATEGY);
    prof_leave(b); prof_leave(a); prof_leave(root);
    prof_report(0,0,0,0);
    return 0;
}
