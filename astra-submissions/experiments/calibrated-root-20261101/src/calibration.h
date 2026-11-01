/* Fitted on TRAIN only; selected on VALIDATION; no arena deployment. */
#ifndef ASTRA_KING_CALIBRATION_H
#define ASTRA_KING_CALIBRATION_H
#include <math.h>
static inline double astra_calibrated_king_loss(double p) {
    if (p < 1e-6) p = 1e-6;
    if (p > 1.0-1e-6) p = 1.0-1e-6;
    const double z = -0.013674074674145501 + 0.54256733229527943 * (log(p)-log1p(-p));
    return 1.0/(1.0+exp(-z));
}
#endif
