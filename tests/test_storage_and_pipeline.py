from datetime import datetime, timezone

from lottery_data_forge.models import Game
from lottery_data_forge.pipeline import normalize_and_store
from lottery_data_forge.storage import Store


def test_valid_draw_is_stored_and_duplicate_is_quarantined(tmp_path) -> None:
    store = Store(tmp_path / "lottery.db")
    source = (
        "2026-09-19|L-1|1,2,3,4,5,6|7\n"
        "2026-09-19|L-1|1,2,3,4,5,6|7"
    )

    valid, invalid = normalize_and_store(
        source,
        game=Game.LOTTO,
        source_url="https://official.example/results",
        source_hash="0" * 64,
        retrieved_at=datetime.now(timezone.utc),
        store=store,
    )

    assert (valid, invalid) == (1, 1)
    assert len(store.iter_draws("lotto")) == 1


def test_raw_hash_is_verified_from_database(tmp_path) -> None:
    store = Store(tmp_path / "lottery.db")
    content = b"captured source"
    import hashlib

    digest = hashlib.sha256(content).hexdigest()
    store.save_raw(digest, "https://official.example/results", "2026-09-28T00:00:00+00:00", content)
    assert store.raw_matches_hash(digest)
