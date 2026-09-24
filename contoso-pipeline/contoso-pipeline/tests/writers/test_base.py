import pytest

from pipeline.models import Batch
from pipeline.writers.base import WriteError, WriteResult, WriterBase


def test_writer_base_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        WriterBase()


def test_subclass_must_implement_write():
    class IncompleteWriter(WriterBase):
        pass

    with pytest.raises(TypeError):
        IncompleteWriter()


def test_subclass_implementing_write_can_be_instantiated():
    class MinimalWriter(WriterBase):
        def write(self, batch: Batch) -> WriteResult:
            return WriteResult(
                destination="memory", records_written=len(batch), succeeded=True
            )

    writer = MinimalWriter()
    result = writer.write(Batch(source_name="test"))

    assert result.succeeded
    assert result.records_written == 0


def test_write_error_carries_its_result():
    partial_result = WriteResult(
        destination="memory", records_written=2, succeeded=False
    )

    error = WriteError("boom", result=partial_result)

    assert error.result is partial_result
    assert error.result.records_written == 2
    assert str(error) == "boom"
