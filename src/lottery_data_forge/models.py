from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Game(str, Enum):
    LOTTO = "lotto"
    POWERBALL = "powerball"
    DAILY_LOTTO = "daily_lotto"


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    QUARANTINED = "quarantined"


class DrawRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game: Game
    draw_date: date
    draw_id: str = Field(min_length=1)
    main_numbers: list[int] = Field(min_length=1)
    bonus_or_powerball: int | None = None
    source_url: str = Field(min_length=1)
    source_retrieved_at: datetime
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rule_version: str = Field(min_length=1)
    validation_status: ValidationStatus

    @field_validator("main_numbers")
    @classmethod
    def numbers_are_unique(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("main_numbers must not contain duplicates")
        return value

    def as_db_tuple(self) -> tuple[object, ...]:
        return (
            self.game.value,
            self.draw_date.isoformat(),
            self.draw_id,
            ",".join(map(str, self.main_numbers)),
            self.bonus_or_powerball,
            self.source_url,
            self.source_retrieved_at.isoformat(),
            self.source_hash,
            self.rule_version,
            self.validation_status.value,
        )
