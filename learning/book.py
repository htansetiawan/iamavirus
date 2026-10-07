"""Write the opening book the bot reads at start-up.

    python -m learning.book --input gold/opening-book.json --output book.txt

One line per entry: colour|observation|move|games|win_rate. The observation is
the 64-character view string the referee sends (rank 1 first), so the bot can
look up its own current view directly.
"""
import argparse
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("gold/opening-book.json"))
    parser.add_argument("--output", type=Path, default=Path("book.txt"))
    parser.add_argument("--min-games", type=int, default=15)
    args = parser.parse_args(argv)
    book = json.loads(args.input.read_text())
    lines = []
    for key, entry in sorted(book["entries"].items()):
        colour, view = key.split("|", 1)
        if entry["games"] < args.min_games:
            continue
        lines.append(f"{colour}|{view}|{entry['move']}|{entry['games']}|{entry['win_rate']:.3f}")
    args.output.write_text("\n".join(lines) + "\n")
    print(f"wrote {len(lines)} book entries to {args.output}")


if __name__ == "__main__":
    main()
