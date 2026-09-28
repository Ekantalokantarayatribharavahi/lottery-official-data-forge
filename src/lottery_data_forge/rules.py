from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleVersion:
    version: str
    main_count: int
    main_min: int
    main_max: int
    bonus_required: bool
    bonus_min: int | None = None
    bonus_max: int | None = None


# The design requires historical rule eras to remain distinct. Only current
# defaults are registered here; historical versions should be added explicitly
# once independently verified from official evidence.
RULES: dict[str, RuleVersion] = {
    "lotto-current": RuleVersion("lotto-current", 6, 1, 52, True, 1, 52),
    "powerball-current": RuleVersion("powerball-current", 5, 1, 50, True, 1, 20),
    "daily_lotto-current": RuleVersion("daily_lotto-current", 5, 1, 36, False),
}


def resolve_rule(game: str, rule_version: str | None = None) -> RuleVersion:
    key = rule_version or f"{game}-current"
    try:
        return RULES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown rule version: {key}") from exc


def validate_numbers(
    main_numbers: list[int], bonus: int | None, rule: RuleVersion
) -> list[str]:
    errors: list[str] = []
    if len(main_numbers) != rule.main_count:
        errors.append(f"expected {rule.main_count} main numbers, got {len(main_numbers)}")
    if len(set(main_numbers)) != len(main_numbers):
        errors.append("main numbers contain duplicates")
    if any(n < rule.main_min or n > rule.main_max for n in main_numbers):
        errors.append(f"main numbers must be in [{rule.main_min}, {rule.main_max}]")

    if rule.bonus_required and bonus is None:
        errors.append("bonus/powerball is required")
    if bonus is not None:
        if rule.bonus_min is None or rule.bonus_max is None:
            errors.append("bonus/powerball is not allowed for this rule")
        elif not rule.bonus_min <= bonus <= rule.bonus_max:
            errors.append(f"bonus/powerball must be in [{rule.bonus_min}, {rule.bonus_max}]")
    return errors
