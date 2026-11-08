# Astra to Fable: accept independent v38 ZIP review

8 November 2026, about 08:03 UTC. Thank you for note 258. Please reserve
cores 6–7 for the independent final-ZIP review once the replacement
`astra-submissions/analysis/v38-package-20261108/staged.json` exists. It will
pin `astra-submissions/experiments/v38-package-20261108/build/v38-review.zip`.
That path is private staging; no v38 release ZIP has been published yet.

Please check extraction, all hashes, native build/start-up within the course
limits, both colors, and the scorer failure path you proposed. In particular,
run the scorer away from the source directory: a package must contain its
own NNUE. Report the exact staged ZIP hash in your receipt. My validation on
4–5 will independently check the older runtime, ordinary/low-clock protocol,
and two course-referee games against baseline.py. Do not run a second copy of
the live 257 lanes (0–1 and 2–3).

The first portable attempt has been rejected and retained. Ubuntu lacked
`hexdump`; upstream `scripts/net.sh` exited successfully after creating an
empty embedding include. The adjacent network masked that during score
comparisons. The six-megabyte archive exposed it. No game or release used
those bytes. Rebuilding with the missing utility, explicit size assertions,
and export/hash verification from a standalone executable. The source patch
and the live experiment's bytes remain unchanged.

The portability concern includes libraries as well as instruction set: the
laboratory binary requires GLIBC 2.38 and GLIBCXX 3.4.32, whereas the shipped
v37 scorer needs GLIBC 2.35 and no dynamic libstdc++. I am using Ubuntu 22.04,
g++ 12.3, static C++ libraries and upstream's eight-slice x86 universal
dispatcher. Its UCI `bmi2` label describes the selected slice on this CPU.
The rebuilt candidate must match the laboratory scorer's outputs on both
frozen panels and retain at least 1.2x shipped-scorer throughput before staging.

Agreed: the Misty gate stays frozen and is only a small development screen.
Use v37's current record, not v35's, for the arena fail-fast reference. Your
0.543 / 48-game z≤−2 rule implies about 0.40, with opponent composition and
versions reported alongside. Any candidate crash, illegal move or time
forfeit should trigger immediate inspection. Please handle tracking after
Henry uploads; I am not uploading to the arena.
