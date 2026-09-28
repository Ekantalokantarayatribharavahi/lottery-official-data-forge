# Official Lottery Data Forge

Reproducible acquisition and validation of official South African lottery draw data.

## CLI

```bash
lottery-data-forge fetch --game lotto --from 2020-01-01 --to 2026-09-28 --source <official-url>
lottery-data-forge validate --game lotto
lottery-data-forge export --game lotto --format csv
```

Raw sources are captured separately and content-addressed by SHA-256. Every normalized draw keeps its source URL, retrieval timestamp, source hash, rule version, and validation status. Invalid observations are quarantined instead of discarded.

### Development

```bash
python -m pip install -e ".[dev]"
pytest
```
