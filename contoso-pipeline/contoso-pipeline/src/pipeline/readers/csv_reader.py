"""Reads customer records from a CSV extract into a Batch."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from pipeline.models import Batch, Record

REQUIRED_COLUMNS = {"record_id", "customer_id", "amount", "recorded_at"}


class CsvReadError(Exception):
    """Raised when a CSV source cannot be read or is malformed."""


def read_csv(source_path: str | Path) -> Batch:
    """Read a CSV file into a Batch of Records.

    The CSV must contain at least the columns `record_id`, `customer_id`,
    `amount` and `recorded_at`. Extra columns are preserved on `Record.raw`
    but do not need to be recognised.

    Args:
        source_path: Path to the CSV file to read.

    Returns:
        A Batch containing one Record per data row, in file order.

    Raises:
        CsvReadError: If the file does not exist, has no header, is missing
            a required column, or a row cannot be parsed.
    """
    path = Path(source_path)
    if not path.exists():
        raise CsvReadError(f"Source file not found: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise CsvReadError(f"Source file has no header row: {path}")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise CsvReadError(
                f"Source file {path} is missing required columns: "
                f"{', '.join(sorted(missing))}"
            )

        records: list[Record] = []
        for line_number, row in enumerate(reader, start=2):
            records.append(_row_to_record(row, path, line_number))

    return Batch(source_name=str(path), records=records)


def _row_to_record(row: dict[str, str], path: Path, line_number: int) -> Record:
    try:
        amount = float(row["amount"])
    except ValueError as exc:
        raise CsvReadError(
            f"{path}:{line_number}: invalid amount value {row['amount']!r}"
        ) from exc

    try:
        recorded_at = datetime.fromisoformat(row["recorded_at"])
    except ValueError as exc:
        raise CsvReadError(
            f"{path}:{line_number}: invalid recorded_at value "
            f"{row['recorded_at']!r}, expected ISO 8601"
        ) from exc

    return Record(
        record_id=row["record_id"],
        customer_id=row["customer_id"],
        amount=amount,
        recorded_at=recorded_at,
        raw=dict(row),
    )
