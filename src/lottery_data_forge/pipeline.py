from __future__ import annotations

import json
from datetime import datetime, timezone

from .models import DrawRecord, Game, ValidationStatus
from .parsers import parse_simple_text
from .rules import resolve_rule, validate_numbers
from .storage import Store


def normalize_and_store(
    raw_text: str,
    *,
    game: Game,
    source_url: str,
    source_hash: str,
    retrieved_at: datetime,
    store: Store,
    rule_version: str | None = None,
) -> tuple[int, int]:
    rule = resolve_rule(game.value, rule_version)
    valid_count = 0
    invalid_count = 0
    existing = {record.draw_id for record in store.iter_draws(game.value)}

    for parsed in parse_simple_text(raw_text, game=game.value):
        errors = validate_numbers(
            parsed.main_numbers, parsed.bonus_or_powerball, rule
        )
        if parsed.draw_id in existing:
            errors.append("duplicate draw ID")

        payload = json.dumps(
            {
                "draw_date": parsed.draw_date.isoformat(),
                "draw_id": parsed.draw_id,
                "main_numbers": parsed.main_numbers,
                "bonus_or_powerball": parsed.bonus_or_powerball,
            },
            sort_keys=True,
        )

        if errors:
            store.quarantine(
                game.value,
                parsed.draw_id,
                payload,
                "; ".join(errors),
                source_hash,
                datetime.now(timezone.utc).isoformat(),
            )
            invalid_count += 1
            continue

        store.insert_draw(
            DrawRecord(
                game=game,
                draw_date=parsed.draw_date,
                draw_id=parsed.draw_id,
                main_numbers=parsed.main_numbers,
                bonus_or_powerball=parsed.bonus_or_powerball,
                source_url=source_url,
                source_retrieved_at=retrieved_at,
                source_hash=source_hash,
                rule_version=rule.version,
                validation_status=ValidationStatus.VALID,
            )
        )
        existing.add(parsed.draw_id)
        valid_count += 1

    return valid_count, invalid_count
