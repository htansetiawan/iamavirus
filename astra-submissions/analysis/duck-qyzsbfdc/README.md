# Duck loss qyzsbfdc: avoidable hidden-rook exposure

[Public game](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qyzsbfdc): arena v10 IAmAVirus, Black, versus Duck v4. White wins after 52 plies, `King capturable`.

After White's **26.Bxg7**, Black played **26...Kb8** (`a7b8`). A White rook on **h8**, hidden in Black's view, attacked b8 along the eighth rank. Ten of the twelve legal moves survived immediate adjudication, including Ka6 and Kb7. This final decision was avoidable; survival does not establish a winning continuation or explain why the bot selected Kb8.

[summary.json](summary.json) records all alternatives, attacker visibility and public replay checksum. The course referee and native rules agree on **53 frames and 1,630 legal-move survival labels**. The replay was captured by the paced public monitor under `/media/henrytan/seagate/iamavirus/astra/arena-monitor/replays/qyzsbfdc.json.gz`.

This is a development diagnostic, completed before the prospective gate cutoff. Keep it separate from `bluqrpex`, whose final decision had no surviving legal move.
