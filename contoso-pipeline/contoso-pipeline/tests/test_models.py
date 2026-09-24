from datetime import datetime

from pipeline.models import Batch, Record


def _make_record(record_id: str = "R1") -> Record:
    return Record(
        record_id=record_id,
        customer_id="C-1",
        amount=19.99,
        recorded_at=datetime(2026, 1, 5, 9, 0, 0),
        raw={"record_id": record_id, "amount": "19.99"},
    )


def test_record_to_dict_contains_expected_keys():
    record = _make_record()

    result = record.to_dict()

    assert result == {
        "record_id": "R1",
        "customer_id": "C-1",
        "amount": 19.99,
        "recorded_at": "2026-01-05T09:00:00",
    }


def test_record_to_dict_excludes_raw():
    record = _make_record()

    result = record.to_dict()

    assert "raw" not in result


def test_batch_len_matches_record_count():
    batch = Batch(source_name="test.csv", records=[_make_record("R1"), _make_record("R2")])

    assert len(batch) == 2


def test_batch_is_iterable_in_order():
    records = [_make_record("R1"), _make_record("R2"), _make_record("R3")]
    batch = Batch(source_name="test.csv", records=records)

    assert list(batch) == records


def test_empty_batch_is_empty():
    batch = Batch(source_name="test.csv")

    assert batch.is_empty
    assert len(batch) == 0


def test_nonempty_batch_is_not_empty():
    batch = Batch(source_name="test.csv", records=[_make_record()])

    assert not batch.is_empty
