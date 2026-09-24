"""Pipeline orchestration entry point: read a source, then write the output."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pipeline.config import load_config
from pipeline.readers.csv_reader import read_csv
from pipeline.writers.base import WriteResult, WriterBase
from pipeline.writers.local_writer import LocalFileWriter

logger = logging.getLogger(__name__)


class UnknownWriterTypeError(Exception):
    """Raised when configuration names a writer type the pipeline does not know."""


def build_writer(writer_config: dict[str, Any]) -> WriterBase:
    """Construct the writer named in configuration.

    Args:
        writer_config: The `writer` section of the pipeline configuration.
            Must contain a `type` key.

    Returns:
        A configured `WriterBase` instance.

    Raises:
        UnknownWriterTypeError: If `writer_config["type"]` does not match a
            known writer.
    """
    writer_type = writer_config["type"]

    if writer_type == "local":
        return LocalFileWriter(output_dir=writer_config["output_dir"])

    raise UnknownWriterTypeError(f"Unknown writer type: {writer_type!r}")


def run(config_path: str | Path | None = None) -> WriteResult:
    """Run one pipeline pass: read the configured source, write the output.

    Args:
        config_path: Optional path to a JSON configuration file. See
            `pipeline.config.load_config` for how overrides are merged.

    Returns:
        The `WriteResult` produced by the configured writer.
    """
    config = load_config(config_path)

    batch = read_csv(config["source_path"])
    logger.info("Read %d record(s) from %s", len(batch), batch.source_name)

    writer = build_writer(config["writer"])
    result = writer.write(batch)
    logger.info(
        "Wrote %d record(s) to %s", result.records_written, result.destination
    )

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
