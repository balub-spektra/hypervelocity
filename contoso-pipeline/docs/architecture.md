# Pipeline Architecture

## Purpose

The Contoso pipeline ingests customer transaction records from a CSV extract
and writes them, normalised, to a durable destination. It runs as a
scheduled batch job, not a service; there is no long-running process and no
public API.

## Flow

```
data/sample_records.csv
        │
        ▼
readers/csv_reader.py  ──▶  Batch[Record]
        │
        ▼
runner.py  (orchestration)
        │
        ▼
writers/*.py  ──▶  destination (local disk today)
```

1. **Read.** `readers/csv_reader.read_csv()` reads a CSV file and returns a
   `Batch` of `Record` objects. Every record is validated at read time:
   `amount` must parse as a float and `recorded_at` must parse as ISO 8601.
   A row that fails either check raises `CsvReadError` immediately; there is
   no "quarantine and continue" behaviour today.

2. **Configure.** `config.py` loads a JSON configuration file (or falls back
   to defaults) describing the source path and which writer to use.
   `runner.build_writer()` turns the `writer` section of that configuration
   into a concrete `WriterBase` instance.

3. **Write.** `runner.run()` passes the batch to the configured writer's
   `write()` method. The writer is responsible for serialising every record
   to its destination and returning a `WriteResult`, or raising `WriteError`
   if it cannot finish.

## Why writers are pluggable

`WriterBase` (`writers/base.py`) exists so the pipeline's orchestration code
in `runner.py` never needs to know which destination it is writing to. Today
there is exactly one implementation, `LocalFileWriter`, which writes to
local disk as newline-delimited JSON. Adding a new destination means adding
a new class that extends `WriterBase` and wiring its type string into
`runner.build_writer()` — nothing else in the pipeline should need to
change.

## Error handling philosophy

The pipeline favours **fail fast with an informative exception** over silent
recovery, at every stage:

- The reader raises `CsvReadError` on the first malformed row rather than
  skipping it.
- A writer raises `WriteError` if it cannot finish a batch, and that
  exception carries a `WriteResult` describing exactly how much of the batch
  was written before the failure. This is what allows a caller to resume
  cleanly rather than re-processing records that already landed at the
  destination. See `docs/conventions.md` for the convention this
  establishes for any new writer.

## Non-goals

- No retry logic lives inside a writer. Retries, if needed, belong in the
  caller (or a future scheduler), because only the caller knows whether
  re-running from the start is safe for a given destination.
- No writer is responsible for reading its own previous output to
  deduplicate. Idempotency is a concern for the layer that decides *when* to
  run the pipeline, not for the writer itself.
