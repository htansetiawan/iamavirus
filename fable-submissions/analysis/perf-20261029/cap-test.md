# Belief cap test: test_belief (mist-c 2803b68, default 2 threads? no: FOW_VERBOSE=1, one core each) on tests/traces-v35.txt (60 v35 games) at caps 200K/500K/1M, cores 2-4, 2026-10-29 21:13-21:45Z
## cap 200000
games 60, plies 5142: true position missing 0 times while exact (112 after the cap); |P| mean 14519 max 200000; update mean 0.0708 s max 3.185 s; games that hit the cap 28 (cap 200000)
truth's weight share while exact (|P| > 1, 3327 plies): geometric mean 0.0063 vs uniform 0.0034 (x1.8); in a 64-world sample 55.7%
## cap 500000
games 60, plies 5142: true position missing 0 times while exact (74 after the cap); |P| mean 25585 max 500000; update mean 0.1241 s max 8.333 s; games that hit the cap 16 (cap 500000)
truth's weight share while exact (|P| > 1, 3921 plies): geometric mean 0.0055 vs uniform 0.0029 (x1.9); in a 64-world sample 55.0%
## cap 1000000
games 60, plies 5172: true position missing 0 times while exact (57 after the cap); |P| mean 38777 max 1000000; update mean 0.1894 s max 16.450 s; games that hit the cap 14 (cap 1000000)
truth's weight share while exact (|P| > 1, 4032 plies): geometric mean 0.0050 vs uniform 0.0026 (x2.0); in a 64-world sample 53.5%

Earlier run at cap 2,000,000 (29 Oct, core 6): games 60, plies 5228, truth missing 33 plies after the cap, |P| mean 54844, update mean 0.2835 s max 35.356 s, games that hit the cap 11.
