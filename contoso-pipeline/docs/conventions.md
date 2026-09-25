# Coding Conventions

These conventions apply to everything under `src/pipeline/` and `tests/`.
They are enforced by the Review phase of any RPI change and by ordinary code
review, whichever comes first.

## Language and typing

- Target Python 3.11+. Use `from __future__ import annotations` at the top
  of every module so modern type-hint syntax (`str | None`, `list[int]`) can
  be used regardless of runtime version.
- Every public function and method has type hints on all parameters and its
  return value. Private helpers (prefixed with `_`) should still be typed
  when the types are not obvious from context.
- Prefer `dataclasses` over plain dictionaries or tuples for any structured
  value that is passed between modules (see `models.Record`,
  `models.Batch`, `writers.base.WriteResult`).

## Naming

- Modules and functions: `snake_case`. Classes: `PascalCase`. Constants:
  `UPPER_SNAKE_CASE`.
- Exception classes end in `Error` (`CsvReadError`, `ConfigError`,
  `WriteError`), not `Exception`.
- A writer class name always ends in `Writer` and matches its module name
  (`LocalFileWriter` in `local_writer.py`). A new blob-backed writer should
  follow the same pairing, e.g. `BlobWriter` in `blob_writer.py`.

## Docstrings

- Google-style docstrings on every public class, function and method: a
  one-line summary, then `Args:`, `Returns:`, and `Raises:` sections when
  applicable. See any function in `readers/csv_reader.py` for the expected
  shape.
- Module-level docstrings describe the module's single responsibility in one
  or two sentences.

## Error handling

- Raise a specific, module-defined exception rather than a bare `Exception`
  or a built-in like `ValueError` at a public boundary. Built-in exceptions
  are fine to catch and re-raise as a domain exception (see
  `csv_reader._row_to_record`), but callers of this codebase should not need
  to catch `ValueError` to handle a pipeline failure.
- **Writers must not roll back partial output.** If a writer cannot finish a
  batch, whatever it already wrote to the destination stays there, and it
  raises `WriteError` carrying a `WriteResult` with an accurate
  `records_written` count. This lets a caller resume from that offset
  instead of re-writing records that already landed. `LocalFileWriter` is
  the reference implementation of this behaviour — any new writer,
  including a Blob Storage writer, must match it rather than inventing a
  different failure contract (e.g. deleting a partially-written blob and
  starting over).
- Never use a bare `except:`. Catch the specific exception type(s) you know
  how to handle.

## Testing

- Every module under `src/pipeline/` has a corresponding `test_*.py` module
  under `tests/`, mirroring the source tree (writers live in
  `tests/writers/`).
- Use `pytest`'s `tmp_path` fixture for any test that touches the
  filesystem. Never write test output into `data/` or the repository root.
- A writer's test suite must include a case that exercises the **partial
  write / failure path**, not just the happy path, because
  `WriteResult.records_written` and `WriteError.result` are part of the
  writer's public contract.
- No network calls in unit tests. A writer that talks to an external service
  (such as Azure Blob Storage) must be testable against a fake or stub
  client, not the real service.

## Imports

- Absolute imports rooted at `pipeline` (e.g. `from pipeline.models import
  Record`), never relative imports (`from ..models import Record`).
- Standard library imports first, then third-party, then local `pipeline`
  imports, each group separated by a blank line.

## Configuration

- New configuration keys are added to `DEFAULT_CONFIG` in `config.py` with a
  sensible default, and validated in `_validate()` if they are required
  rather than optional. Do not read `os.environ` directly from inside a
  writer or reader — configuration flows in through `config.py` only.
