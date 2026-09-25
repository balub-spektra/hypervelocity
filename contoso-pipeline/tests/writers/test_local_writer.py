import json
from datetime import datetime

import pytest

from pipeline.models import Batch, Record
from pipeline.writers.base import WriteError
from pipeline.writers.local_writer import LocalFileWriter


def _record(record_id: str, amount=10.0) -> Record:
    return Record(
        record_id=record_id,
        customer_id="C-1",
        amount=amount,
        recorded_at=datetime(2026, 1, 5, 9, 0, 0),
    )


def test_write_creates_jsonl_file_with_one_line_per_record(tmp_path):
    batch = Batch(source_name="orders.csv", records=[_record("R1"), _record("R2")])
    writer = LocalFileWriter(output_dir=tmp_path)

    result = writer.write(batch)

    assert result.succeeded
    assert result.records_written == 2

    output_file = tmp_path / "orders.jsonl"
    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["record_id"] == "R1"
    assert json.loads(lines[1])["record_id"] == "R2"


def test_write_creates_output_dir_if_missing(tmp_path):
    output_dir = tmp_path / "nested" / "output"
    batch = Batch(source_name="orders.csv", records=[_record("R1")])
    writer = LocalFileWriter(output_dir=output_dir)

    writer.write(batch)

    assert output_dir.exists()
    assert (output_dir / "orders.jsonl").exists()


def test_source_name_is_sanitised_for_the_output_filename(tmp_path):
    batch = Batch(source_name="data/weird name!.csv", records=[_record("R1")])
    writer = LocalFileWriter(output_dir=tmp_path)

    result = writer.write(batch)

    assert result.destination.endswith("weird_name_.jsonl")


def test_partial_write_failure_leaves_earlier_records_on_disk(tmp_path):
    """A record that fails to serialise must not roll back earlier records.

    This matches the behaviour documented in docs/conventions.md: a writer
    leaves whatever it already wrote in place and reports an accurate
    records_written count so a caller can resume from that offset instead of
    rewriting records that already landed at the destination.
    """
    good_record = _record("R1", amount=10.0)
    unserialisable_record = _record("R2", amount=object())  # breaks json.dumps
    never_reached_record = _record("R3", amount=30.0)

    batch = Batch(
        source_name="orders.csv",
        records=[good_record, unserialisable_record, never_reached_record],
    )
    writer = LocalFileWriter(output_dir=tmp_path)

    with pytest.raises(WriteError) as exc_info:
        writer.write(batch)

    error = exc_info.value
    assert error.result.records_written == 1
    assert not error.result.succeeded

    output_file = tmp_path / "orders.jsonl"
    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["record_id"] == "R1"


def test_partial_write_excludes_the_failing_and_later_records(tmp_path):
    batch = Batch(
        source_name="orders.csv",
        records=[_record("R1"), _record("R2", amount=object()), _record("R3")],
    )
    writer = LocalFileWriter(output_dir=tmp_path)

    with pytest.raises(WriteError):
        writer.write(batch)

    output_file = tmp_path / "orders.jsonl"
    written_ids = [
        json.loads(line)["record_id"]
        for line in output_file.read_text(encoding="utf-8").splitlines()
    ]
    assert "R2" not in written_ids
    assert "R3" not in written_ids
