from lottery_data_forge.models import Game
from lottery_data_forge.rules import resolve_rule, validate_numbers


def test_lotto_rule_accepts_valid_numbers() -> None:
    rule = resolve_rule(Game.LOTTO.value, "lotto-current")
    assert validate_numbers([1, 2, 3, 4, 5, 6], 7, rule) == []


def test_lotto_rule_rejects_duplicates_and_range() -> None:
    rule = resolve_rule(Game.LOTTO.value, "lotto-current")
    errors = validate_numbers([1, 2, 3, 3, 5, 99], 7, rule)
    assert "main numbers contain duplicates" in errors
    assert "main numbers must be in [1, 52]" in errors


def test_daily_lotto_does_not_allow_bonus() -> None:
    rule = resolve_rule(Game.DAILY_LOTTO.value, "daily_lotto-current")
    assert any(
        "not allowed" in e
        for e in validate_numbers([1, 2, 3, 4, 5], 10, rule)
    )
