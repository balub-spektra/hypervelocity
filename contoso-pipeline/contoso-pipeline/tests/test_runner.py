import json

import pytest

from pipeline import runner
from pipeline.writers.local_writer import LocalFileWriter

SAMPLE_CSV = """record_id,customer_id,amount,recorded_at
R1,C-1,10.00,2026-01-05T09:00:00
R2,C-2,20.00,2026-01-05T09:05:00
"""


def test_build_writer_returns_local_file_writer_for_local_type(tmp_path):
    writer = runner.build_writer({"type": "local", "output_dir": str(tmp_path)})

    assert isinstance(writer, LocalFileWriter)


def test_build_writer_raises_for_unknown_type():
    with pytest.raises(runner.UnknownWriterTypeError):
        runner.build_writer({"type": "carrier-pigeon"})


def test_run_reads_source_and_writes_output(tmp_path):
    source_path = tmp_path / "input.csv"
    source_path.write_text(SAMPLE_CSV, encoding="utf-8")

    output_dir = tmp_path / "output"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "source_path": str(source_path),
                "writer": {"type": "local", "output_dir": str(output_dir)},
            }
        ),
        encoding="utf-8",
    )

    result = runner.run(config_path)

    assert result.succeeded
    assert result.records_written == 2

    written_lines = (
        (output_dir / "input.jsonl").read_text(encoding="utf-8").splitlines()
    )
    assert len(written_lines) == 2
    first_row = json.loads(written_lines[0])
    assert first_row["record_id"] == "R1"
    assert first_row["amount"] == 10.00


def test_run_uses_default_config_when_no_path_given(monkeypatch, tmp_path):
    source_path = tmp_path / "input.csv"
    source_path.write_text(SAMPLE_CSV, encoding="utf-8")
    output_dir = tmp_path / "output"

    monkeypatch.setattr(
        runner,
        "load_config",
        lambda config_path=None: {
            "source_path": str(source_path),
            "writer": {"type": "local", "output_dir": str(output_dir)},
        },
    )

    result = runner.run()

    assert result.succeeded
    assert result.records_written == 2
