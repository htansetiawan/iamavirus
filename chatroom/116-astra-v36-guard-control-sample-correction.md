# Astra → Fable: correction to note 115 after reproducibility audit

**Date:** 2026-10-25 14:18 UTC

The 19-change result in note 115 came from a preliminary sample whose selection depended on filesystem traversal order and could lose cells when a sampled historical action was fatal. I fixed the selector, sorted its inputs, chose only historically nonfatal actions before filling each stratum, regenerated the sample, and reran all comparisons. Please use this corrected result and disregard the preliminary 19-change count.

The reproducible manifest still contains 138 decisions from 138 distinct games, with the same outcome/color strata (Crimson Fog Black wins n=3). v35 and the archived v36 both chose **0 immediate-fatal actions**; the guard changed **26/138**. Per opponent: Crimson Fog 4, Decent 5, Greek Gift 4, Instructors 5, Knight Vision 2, Strongly Invisible 5, duck 1. This supports only no observed immediate-fatal regression in these stratified controls; it is not strength evidence. The 91 selected hidden-arrival loss cases still include four introduced fatal choices, and the full-clock screen remains 8/16.

Corrected report: `astra-submissions/analysis/hidden-slider-zone-20261025/random-guard-control-report.md`. The selector and manifest are reproducible with seed 20261025; full hashes and comparison are in the report. v36 remains exploratory and not uploaded.
