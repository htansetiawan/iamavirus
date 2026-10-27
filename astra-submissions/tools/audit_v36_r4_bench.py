#!/usr/bin/env python3
"""The unchanged v36 screen/auditor with r4's declared seed schedule.

Separate entrypoint keeps r3's evidence and reproducibility intact. Counts,
thresholds, artifact checks, receipt requirements and replay checks are shared.
"""
import audit_v36_bench as audit

audit.ROLES = {
    'direct': (40, 300000),
    'candidate_misty': (32, 301000),
    'baseline_misty': (32, 301000),
}

if __name__ == '__main__':
    raise SystemExit(audit.main())
