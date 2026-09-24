# Contoso Pipeline

A small internal data pipeline used by Contoso Data Services to ingest customer
records from CSV extracts, validate and normalise them, and write the
processed output somewhere durable.

## What it does

1. `readers/csv_reader.py` reads a batch of records from a CSV file.
2. `models.py` defines the `Record` and `Batch` shapes the rest of the
   pipeline passes around.
3. `runner.py` orchestrates a run: read → validate → write.
4. `writers/` contains the output writers. Today there is only
   `LocalFileWriter`, which writes processed batches to local disk as JSON
   Lines. **Output is local-disk only.**

## Backlog

Customers have asked for pipeline output to also land in **Azure Blob
Storage**, not just local disk. That work has not started yet — this repo is
the starting point for it.

## Getting started

```bash
pip install -r requirements.txt
pytest -q
```

Both commands should complete cleanly before you make any changes. If either
fails on a fresh checkout, fix that first.

## Project layout

```
contoso-pipeline/
├── src/
│   └── pipeline/
│       ├── __init__.py
│       ├── runner.py                  # Pipeline orchestration entry point
│       ├── models.py                  # Record and batch data models
│       ├── config.py                  # Configuration loading
│       ├── readers/
│       │   ├── __init__.py
│       │   └── csv_reader.py          # Source data reader
│       └── writers/
│           ├── __init__.py
│           ├── base.py                # WriterBase abstract class
│           └── local_writer.py        # LocalFileWriter (existing implementation)
│
├── tests/
│   ├── test_runner.py
│   ├── test_models.py
│   └── writers/
│       ├── test_base.py
│       └── test_local_writer.py
│
├── data/
│   └── sample_records.csv             # Sample input data
│
├── docs/
│   ├── architecture.md                # Pipeline design notes
│   └── conventions.md                 # Team coding conventions
│
├── .copilot-tracking/                 # RPI artifacts land here (git-ignored)
├── requirements.txt
├── pytest.ini
└── README.md
```

See `docs/architecture.md` for how the pieces fit together and
`docs/conventions.md` for the coding conventions this codebase follows.
