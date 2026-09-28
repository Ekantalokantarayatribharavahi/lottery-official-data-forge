from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .capture import capture_url
from .exporter import export_csv
from .models import Game
from .pipeline import normalize_and_store
from .rules import resolve_rule, validate_numbers
from .storage import Store


DEFAULT_DB = Path("data/lottery.db")
DEFAULT_RAW = Path("data/raw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lottery-data-forge")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Capture and normalize an official source")
    fetch.add_argument("--game", choices=[g.value for g in Game], required=True)
    fetch.add_argument("--from", dest="date_from", type=date.fromisoformat, required=True)
    fetch.add_argument("--to", dest="date_to", type=date.fromisoformat, required=True)
    fetch.add_argument("--source", action="append", default=[], help="Official source URL")
    fetch.add_argument("--rule-version")
    fetch.add_argument("--db", type=Path, default=DEFAULT_DB)
    fetch.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)

    validate = sub.add_parser("validate", help="Validate stored draws and source integrity")
    validate.add_argument("--game", choices=[g.value for g in Game], required=True)
    validate.add_argument("--db", type=Path, default=DEFAULT_DB)

    export = sub.add_parser("export", help="Export normalized draws")
    export.add_argument("--game", choices=[g.value for g in Game], required=True)
    export.add_argument("--format", choices=["csv"], required=True)
    export.add_argument("--output")
    export.add_argument("--db", type=Path, default=DEFAULT_DB)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "fetch":
        if args.date_to < args.date_from:
            raise SystemExit("--to must be on or after --from")
        if not args.source:
            raise SystemExit("fetch requires at least one --source official URL")

        store = Store(args.db)
        for url in args.source:
            capture = capture_url(url, args.raw_dir, store)
            text = capture.content.decode("utf-8", errors="strict")
            selected_lines: list[str] = []

            for line in text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    selected_lines.append(line)
                    continue
                date_text = stripped.split("|", 1)[0].strip()
                try:
                    draw_date = date.fromisoformat(date_text)
                except ValueError:
                    continue
                if args.date_from <= draw_date <= args.date_to:
                    selected_lines.append(line)

            valid, invalid = normalize_and_store(
                "\n".join(selected_lines),
                game=Game(args.game),
                source_url=capture.source_url,
                source_hash=capture.source_hash,
                retrieved_at=capture.retrieved_at,
                store=store,
                rule_version=args.rule_version,
            )
            print(f"{url}: valid={valid} quarantined={invalid}")
        return 0

    store = Store(args.db)

    if args.command == "validate":
        for record in store.iter_draws(args.game):
            rule = resolve_rule(record.game.value, record.rule_version)
            errors = validate_numbers(
                record.main_numbers, record.bonus_or_powerball, rule
            )
            if not store.raw_matches_hash(record.source_hash):
                errors.append("raw source hash mismatch")
            if errors:
                print(f"{record.draw_id}: invalid: {'; '.join(errors)}")
                return 1
        print("validation passed")
        return 0

    if args.command == "export":
        export_csv(store, args.game, args.output)
        return 0

    return 1
