"""Abstract base class every output writer must extend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pipeline.models import Batch


@dataclass
class WriteResult:
    """Outcome of a single `WriterBase.write()` call.

    Attributes:
        destination: Human-readable description of where the batch was
            written (a file path, a blob URL, etc.), for logging.
        records_written: Number of records successfully written before any
            failure. On full success this equals the batch length.
        succeeded: True only if every record in the batch was written.
    """

    destination: str
    records_written: int
    succeeded: bool


class WriteError(Exception):
    """Raised when a writer cannot complete writing a batch.

    Attributes:
        result: The partial WriteResult describing how much of the batch was
            written before the failure. Callers can use this to decide
            whether a retry needs to skip already-written records rather
            than writing the whole batch again.
    """

    def __init__(self, message: str, result: WriteResult):
        super().__init__(message)
        self.result = result


class WriterBase(ABC):
    """Base class every output writer must extend.

    A concrete writer is responsible for:

    - Attempting to write every record in the batch, in order.
    - On full success, returning a `WriteResult` with `succeeded=True` and
      `records_written` equal to the batch length.
    - On partial failure, raising `WriteError` with a `WriteResult`
      describing exactly how many records were written before the failure.
      See `local_writer.LocalFileWriter` for the reference implementation of
      this behaviour.
    - Never leaving a partially-serialised record at the destination. A
      given record is either fully written or not written at all; only the
      *count* of complete records written may be partial.

    Writers are not required to be reusable across multiple `write()` calls
    unless they document otherwise.
    """

    @abstractmethod
    def write(self, batch: Batch) -> WriteResult:
        """Write every record in `batch` to this writer's destination.

        Args:
            batch: The batch of records to write.

        Returns:
            A WriteResult describing the outcome.

        Raises:
            WriteError: If the batch could not be fully written. The
                exception carries a WriteResult describing how many records
                were written before the failure occurred.
        """
        raise NotImplementedError
