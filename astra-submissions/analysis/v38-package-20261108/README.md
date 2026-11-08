# V38 package checks — in progress

The staged review ZIP is **84,989,047 bytes**, SHA256
`ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
It is under `experiments/v38-package-20261108/build/v38-review.zip`; no numbered
release has been published. Promotion still requires the independent matched
Misty gate and the completed archive checks.

The portable scorer embeds the original 98,511,183-byte NNUE, verified by
exporting it from a standalone executable. It uses the original eight-slice
x86 dispatcher, static C++ runtime, and glibc 2.35. The native C sources,
learned move model and history table are byte-identical to v37's archive.

The 3,072 query pairs match the laboratory candidate's scores, best choices
and node counts. Sixty-four special-case calls also pass. Median throughput
relative to the shipped v37 scorer is 1.566x played/cold, 1.632x played/warm,
1.632x search-frontier/cold and 1.681x search-frontier/warm. These are scorer
checks on reused development panels, not an Elo estimate.

The exact ZIP builds and produces a legal first move in an offline Ubuntu
22.04 container limited to two cores, 4 GiB and 64 processes. Four two-turn
protocol probes pass, both colors at 180 and two seconds; maximum measured
startup is 0.771 s. Full-clock, turn-isolated games against baseline.py are
running as archive correctness checks. Fable has the hash for independent
review. This is a compatibility approximation, not the arena's exact gVisor
image.

Retained failures:

- `invalid-attempt0/`: missing `hexdump` caused upstream's network build script
  to emit an empty embedding while returning success. Adjacent weights masked
  it during score checks. The undersized ZIP was rejected before any game or
  release; the repaired binary passes standalone export/hash validation.
- `clock-probe.md`: candidate and unchanged v37 both fail an artificial
  0.2-second prompt because the inherited solver uses 0.3 seconds. Actual
  180+2 turn prompts are at least two seconds. The impossible-history probe
  remains recorded; the reachable minimum is tested separately.
