from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ParsedDraw:
    draw_date: date
    draw_id: str
    main_numbers: list[int]
    bonus_or_powerball: int | None


DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")


def parse_simple_text(text: str, *, game: str) -> list[ParsedDraw]:
    """Parse the deterministic interchange format used by tests and fixtures.

    Expected form:
        YYYY-MM-DD|draw-id|n1,n2,n3,...|bonus_or_powerball

    The game argument is intentionally retained at the parser boundary so a
    future HTML parser can apply game-specific extraction without changing the
    pipeline contract.
    """
    del game
    draws: list[ParsedDraw] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            raise ValueError(f"Invalid fixture line: {line!r}")

        if not DATE_RE.fullmatch(parts[0]):
            raise ValueError(f"Invalid date: {parts[0]!r}")

        try:
            draw_date = date.fromisoformat(parts[0])
            numbers = [int(x.strip()) for x in parts[2].split(",") if x.strip()]
            bonus = int(parts[3]) if parts[3] else None
        except ValueError as exc:
            raise ValueError(f"Invalid numeric/date field: {line!r}") from exc

        if not parts[1]:
            raise ValueError("draw_id must not be empty")

        draws.append(ParsedDraw(draw_date, parts[1], numbers, bonus))

    return draws
