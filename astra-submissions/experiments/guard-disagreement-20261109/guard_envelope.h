/* Experimental action support under disagreement between two risk models.
 * Keep when within margin under either model. This is not a safety guarantee.
 * Disabled preserves the deployed two-pass predicate exactly.
 */
#ifndef ASTRA_GUARD_ENVELOPE_H
#define ASTRA_GUARD_ENVELOPE_H
static inline int astra_guard_excluded(double risk, double sharp,
                                       double least, double least_sharp,
                                       double margin, int pass, int either) {
    if (either) return sharp > least_sharp + margin && risk > least + margin;
    return sharp > least_sharp + margin || (pass == 0 && risk > least + margin);
}
#endif
