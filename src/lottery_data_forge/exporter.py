from __future__ import annotations

import csv
import sys

from .storage import Store

FIELDS = [
    "game",
    "draw_date",
    "draw_id",
    "main_numbers",
    "bonus_or_powerball",
    "source_url",
    "source_retrieved_at",
    "source_hash",
    "rule_version",
    "validation_status",
]


def export_csv(store: Store, game: str, output: str | None = None) -> None:
    rows = store.iter_draws(game)
    target = open(output, "w", newline="", encoding="utf-8") if output else sys.stdout
    try:
        writer = csv.writer(target)
        writer.writerow(FIELDS)
        for row in rows:
            writer.writerow(
                [
                    row.game.value,
                    row.draw_date.isoformat(),
                    row.draw_id,
                    ",".join(map(str, row.main_numbers)),
                    row.bonus_or_powerball,
                    row.source_url,
                    row.source_retrieved_at.isoformat(),
                    row.source_hash,
                    row.rule_version,
                    row.validation_status.value,
                ]
            )
    finally:
        if output:
            target.close()
