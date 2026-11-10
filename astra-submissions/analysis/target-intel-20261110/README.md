# Priority-opponent refresh: first bounded batch

**Partial collection; retained data independently verified.** Original session 15923 exited 1 at its request bound. It made 495 HTTP attempts in 776 seconds, added 451 accepted replays, and quarantined none. This remains a partial attempt; it is not relabelled complete.

The independent course audit verifies all 451 additions and every cached replay used in the completed taxonomy: **615 distinct games / 55,966 frames**. It checks moves, both views, boards, clocks, terminal outcomes, stored-byte hashes, accepted move hashes and the complete initial journal prefix. Taxonomy counts recompute exactly.

| Team | Active version | Normal games | Unseen king threats /100 moves | King moves /100 | Unseen queen exposure /100 | Walk into unseen /100 |
|---|---:|---:|---:|---:|---:|---:|
| duck | 11 | 199 | 1.73 | 14.22 | 0.08 | 2.12 |
| Instructors | 4 | 198 | 1.77 | 13.74 | 0.13 | 2.82 |
| HYPOTHERMIA | 4 | 196 | 1.44 | 14.50 | 0.17 | 3.04 |

Each search lists the latest 200 games. Technical games and older versions are excluded from the taxonomy; colors, phases and opponent schedules remain mixed. These descriptive rates do not rank true skill or justify an automatic evaluation penalty.

Duck and Instructors cover roughly November 9 05:50 UTC through November 10 00:50 UTC. Exact boundaries and exclusions are in each team JSON. Greek Gift has 43 newly accepted games in this partial batch but no completed taxonomy. Mist Opportunities was not reached. A separately bounded continuation will collect those two teams from a new metadata snapshot, reusing completed immutable games.

The accepted-ID cache fast path reuses previously validated records. Existing transport hashes describe the HTTP JSON encoding; stored JSON is reserialized and has its own byte hash. The independent audit covers both newly added and taxonomized cached replays, rather than claiming a transport-byte cache check occurred on every fast-path read.

All raw replays remain in the shared bulk-disk corpus. No tested engine, prior coefficient, history table or guard changed. A model fit needs its own time split and predictive/playing gates.

See [receipt.json](receipt.json), [audit.json](audit.json), original API pages under listings/, and new-games.jsonl.
