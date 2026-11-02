# Arena versions 36 and 37: archive mapping audit

2 November 2026. One public GET of the team's version list verifies the
submission creation times and active flags below. The raw response and its
fetch timestamp/hash are preserved. API `createdAt` is a submission creation
time, not proof of when the human activated it. The public API does not expose
the uploaded ZIP checksum; archive associations rely on the team's recorded
upload/release notes, with independent local archive/source verification.

| Arena version | API creation time, UTC | Recorded archive | SHA-256 prefix | Source commit | API status |
|---|---|---|---|---|---|
| 36 | 2026-10-27 23:23:45 | `fable-submissions/iamavirus-v36-candidate-mist-c-v20-r4.zip` | `1649dfbfe23b` | `dd8990739c8b` | Inactive, 16W–1D–33L / 50 games |
| 37 | 2026-11-01 14:29:11 | `fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip` | `41e02e280b61` | `f76a09e2f58b` | Active, 98W–8D–90L / 196 games |

All 19 `src/*.c` / `src/*.h` files in **each** archive match its named commit
byte for byte, and both ZIP CRC checks pass. `mapping.json` and
`mapping-v36.json` preserve full hashes and the source-file hashes. The v37
record additionally pins its run/build scripts, Stockfish, and history table.
Original collector handle 65468 exited 0. The v36 audit was offline against
the same saved API response and exited 0; no second API request was made.

The archive association for v36 is the human-upload report in `MUTATIONS.md`.
For v37 it is Fable's `chatroom/192-fable-v37-allgames-refit.md`. No new claim
of cryptographically verified remote bytes is made.

The old Astra `iamavirus-v36-kingguard0001.zip` is **a withdrawn local label,
never uploaded**. It is distinct from the actual arena v36 r4 archive. The
shared submission map now labels that historical Astra row accordingly and
adds the actual v36 and v37 metadata. No archive has been renamed, overwritten,
or uploaded by this bookkeeping change.
