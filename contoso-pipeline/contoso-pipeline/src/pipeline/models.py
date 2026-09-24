"""Data models shared across the pipeline.

`Record` represents a single normalised row of customer data. `Batch` is an
ordered collection of records produced by a single reader run, tagged with
the source name it came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Record:
    """A single validated row of pipeline data.

    Attributes:
        record_id: Stable identifier for the row, taken from the source data.
        customer_id: The Contoso customer this record belongs to.
        amount: Monetary amount associated with the record, in the source
            currency's minor units are NOT used here -- this is a plain
            decimal amount (e.g. 19.99).
        recorded_at: When the underlying event occurred, per the source data.
        raw: The original field values as read from the source, kept for
            traceability and debugging.
    """

    record_id: str
    customer_id: str
    amount: float
    recorded_at: datetime
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of this record."""
        return {
            "record_id": self.record_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class Batch:
    """An ordered collection of records read from a single source.

    Attributes:
        source_name: Name of the source the records were read from, e.g. a
            file path or table name.
        records: The records in this batch, in read order.
    """

    source_name: str
    records: list[Record] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    @property
    def is_empty(self) -> bool:
        return len(self.records) == 0
