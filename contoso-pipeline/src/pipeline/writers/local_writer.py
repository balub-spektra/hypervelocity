"""LocalFileWriter: writes a batch to local disk as newline-delimited JSON."""

from __future__ import annotations

from pathlib import Path

from pipeline.models import Batch
from pipeline.writers.base import WriteError, WriteResult, WriterBase

import json


class LocalFileWriter(WriterBase):
    """Writes a batch to local disk as newline-delimited JSON (`.jsonl`).

    One output file is written per batch, named after the batch's
    `source_name` with a `.jsonl` extension, inside `output_dir`.

    Records are written one at a time and the file handle is flushed after
    each record. If a record fails to serialise, writing stops immediately:
    every record written before the failure stays on disk exactly as
    written, and the failing record and everything after it are not
    written. This is deliberate partial-write behaviour, not a bug: a caller
    that catches `WriteError` can inspect `error.result.records_written` and
    resume from that offset instead of re-writing records that are already
    safely on disk. Any new writer added to this package should match this
    behaviour rather than rolling back a partially written destination.
    """

    def __init__(self, output_dir: str | Path):
        """Create a writer that writes batches under `output_dir`.

        Args:
            output_dir: Directory to write output files into. Created if it
                does not already exist.
        """
        self._output_dir = Path(output_dir)

    def write(self, batch: Batch) -> WriteResult:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        destination = self._output_dir / f"{_safe_stem(batch.source_name)}.jsonl"

        records_written = 0
        with destination.open("w", encoding="utf-8") as handle:
            for record in batch:
                try:
                    line = json.dumps(record.to_dict())
                except (TypeError, ValueError) as exc:
                    result = WriteResult(
                        destination=str(destination),
                        records_written=records_written,
                        succeeded=False,
                    )
                    raise WriteError(
                        f"Failed to write record {records_written + 1} of "
                        f"{len(batch)} to {destination}: {exc}",
                        result=result,
                    ) from exc

                handle.write(line + "\n")
                handle.flush()
                records_written += 1

        return WriteResult(
            destination=str(destination),
            records_written=records_written,
            succeeded=True,
        )


def _safe_stem(source_name: str) -> str:
    """Turn a source path or name into a filesystem-safe file stem."""
    stem = Path(source_name).stem or "batch"
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stem)
