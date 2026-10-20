"""Generate a seeded naturalistic-interaction demonstration trace."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .model import NaturalisticInteractionEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a naturalistic pointer trace")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="mixed", choices=["mixed", *NaturalisticInteractionEngine.models])
    parser.add_argument("--output", type=Path, default=Path("trace.csv"))
    args = parser.parse_args()

    generator = NaturalisticInteractionEngine(seed=args.seed)
    selected, points = generator.trajectory((90, 120), (850, 470), target_width=44, model=args.model)
    with args.output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["model", "t_seconds", "x", "y"])
        writer.writerows((selected, round(p.t, 6), round(p.x, 3), round(p.y, 3)) for p in points)
    print(f"wrote {len(points)} {selected} samples to {args.output}")


if __name__ == "__main__":
    main()
