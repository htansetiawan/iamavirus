# Standalone runtime readiness: compatible, not promoted

2 November 2026. The frozen persistent-mode candidate can now be built and launched from an isolated, relocated runtime directory. **No ZIP or version reservation was created.** The running Misty comparison and its original binaries, model and gate are unchanged.

## Found and repaired

The inherited build script omitted the added response, adapter and proof compilation units; the standalone script includes all 13 C files. The runtime script resolves Stockfish, the history table and the 273,684-byte student relative to its own directory, selects the frozen 0.25 persistent mode, and rejects a missing required model before starting the engine.

The first check passed GCC and g++'s C front end, then failed the C++ fallback: dbr_install jumped over the initialized declaration of its response-cache key. The packaging copy now declares the key before the jump and assigns it at the original execution point. `r2/cpp-compat.diff` is the complete source change. Initial failure logs and the original check script are retained; no playing source was modified.

## Verification

| Build route | Build time on reserved cores 4–5 | Relocated protocol checks |
|---|---:|---|
| GCC C11 | 1.91 s | Two legal decisions each as White and Black |
| g++ C front end | 2.00 s | Two legal decisions each as White and Black |
| g++ C++20 fallback | 2.97 s | Two legal decisions each as White and Black |

The GCC rebuild is **byte-for-byte identical** to the playing candidate: `00dc640d9773296b7af7f35b9faceb7f1b2ea6e49199742091415825e5744056`. Each protocol check starts from `/tmp`, loads the local Stockfish/history/student, emits only protocol responses, and confirms persistent-mode activation with no input/key/model errors. Missing-model startup fails explicitly.

Four deterministic native comparisons also match the already-checked C implementation under C++: confidence 0, 0.25 and 1, plus the three-ply fixture for shared own information sets, separate opponent information sets and persistent modes. This is build/runtime correctness, not extra playing-strength evidence. The local compilers are GCC/g++ 13.3; arena compiler 12.2 was not available for a direct test. Build times below 15 seconds here do not guarantee timing on different hardware, and these short smoke tests are not a worst-case memory test.

`r2/implementation-origin.json` records the baseline archive, unchanged trial binary, model/asset/source hashes and the standalone file inventory. The candidate's original provenance is rechecked after all tests. `terminal.json` confirms the readiness processes and workers exited. Next archive number would currently be 38 because Fable's highest archive is 37; this is unreserved and must be checked again at packaging and publication.

Reproduce in a fresh work/output directory with `astra-submissions/experiments/persistent-readiness-20261102/check.py`. It refuses to overwrite existing attempts. The existing hybrid-only release packager must not be used blindly for this C runtime; its +1 numbering function is reused, while archive creation remains gated on the match review.
