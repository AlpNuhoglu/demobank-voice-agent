"""Reset the database and load synthetic seed data.

Usage: uv run python -m scripts.seed [--now 2026-10-01T12:00:00+03:00]

WARNING: drops and recreates ALL tables.
"""

import argparse
from datetime import datetime

from app.config import TIMEZONE
from app.db import engine
from app.services.seed import istanbul_now, seed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--now",
        type=datetime.fromisoformat,
        default=None,
        help="Reference time (ISO 8601). Naive values are Istanbul time. Defaults to now.",
    )
    args = parser.parse_args()
    now = args.now or istanbul_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=TIMEZONE)
    summary = seed(engine, now)
    print(
        f"Seeded {summary.customers} customers, {summary.cards} cards, "
        f"{summary.transactions} transactions (now={now.isoformat()})."
    )


if __name__ == "__main__":
    main()
