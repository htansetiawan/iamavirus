#!/usr/bin/env python3
"""Export the selected fitted curve to C and verify inference parity.

This primitive is not integrated into the game-playing policy here.
"""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from fit import predict

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SOURCE=ROOT/'astra-submissions/analysis/king-event-calibration-20261101/calibration.json'
report=json.loads(SOURCE.read_text());assert report['earns_engine_experiment']
assert report['selected_on_validation']=='calibrated_sharp'
model=report['model'];header=HERE/'calibration.h'
header.write_text('''/* Fitted on TRAIN only; selected on VALIDATION; no arena deployment. */
#ifndef ASTRA_KING_CALIBRATION_H
#define ASTRA_KING_CALIBRATION_H
#include <math.h>
static inline double astra_calibrated_king_loss(double p) {
    if (p < 1e-6) p = 1e-6;
    if (p > 1.0-1e-6) p = 1.0-1e-6;
    const double z = %.17g + %.17g * (log(p)-log1p(-p));
    return 1.0/(1.0+exp(-z));
}
#endif
'''%(model['intercept'],model['slope']))
wrapper=HERE/'build/calibrator_wrapper.c'
wrapper.write_text('#include "../calibration.h"\ndouble evaluate(double p){return astra_calibrated_king_loss(p);}\n')
subprocess.run(['gcc','-O2','-std=c11','-shared','-fPIC',str(wrapper),'-lm','-o',str(HERE/'build/calibrator.so')],check=True)
library=ctypes.CDLL(str(HERE/'build/calibrator.so'));library.evaluate.argtypes=[ctypes.c_double];library.evaluate.restype=ctypes.c_double
values=np.unique(np.concatenate(([0.,1.,1e-300],np.geomspace(1e-12,.5,2000),1-np.geomspace(1e-12,.5,2000),np.linspace(0,1,2001))))
want=predict(values,model);got=np.array([library.evaluate(float(p)) for p in values])
error=float(np.max(np.abs(want-got)));assert error<1e-12,error
assert np.all(np.diff(got)>=-1e-15)
receipt={'model_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         'header_sha256':hashlib.sha256(header.read_bytes()).hexdigest(),'points':len(values),
         'max_absolute_error':error,'coefficient_bytes':16,'deployment':'not wired into policy; no archive or promotion'}
(HERE/'export-parity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
