from pathlib import Path

from lottery_data_forge.parsers import parse_simple_text


def test_parser_fixture() -> None:
    text = Path("tests/fixtures/lotto.txt").read_text(encoding="utf-8")
    draws = parse_simple_text(text, game="lotto")
    assert len(draws) == 2
    assert draws[0].draw_id == "L-20260919-001"
    assert draws[0].main_numbers == [1, 7, 14, 23, 31, 45]
