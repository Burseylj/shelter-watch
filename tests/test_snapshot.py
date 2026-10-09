import gzip
import json

import pytest
from botocore.exceptions import ClientError

from snapshot import save_snapshot


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.head_error_code = "404"

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": self.head_error_code}}, "HeadObject")

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[Key] = Body


RECORDS = [
    {"_id": 1, "OCCUPIED_ROOMS": 10},
    {"_id": 2, "OCCUPIED_ROOMS": 20},
]


def test_first_save_writes_object():
    s3 = FakeS3()
    key = save_snapshot(s3, "b", "2026-09-22", RECORDS)
    assert key in s3.objects
    payload = json.loads(gzip.decompress(s3.objects[key]))
    assert payload["date"] == "2026-09-22"
    assert len(payload["records"]) == 2


def test_identical_data_is_not_written_twice():
    s3 = FakeS3()
    save_snapshot(s3, "b", "2026-09-22", RECORDS)
    assert save_snapshot(s3, "b", "2026-09-22", RECORDS) is None
    assert len(s3.objects) == 1


def test_record_order_does_not_change_the_hash():
    s3 = FakeS3()
    k1 = save_snapshot(s3, "b", "2026-09-22", RECORDS)
    assert save_snapshot(s3, "b", "2026-09-22", list(reversed(RECORDS))) is None
    assert len(s3.objects) == 1 and k1 in s3.objects


def test_changed_data_creates_second_version():
    s3 = FakeS3()
    save_snapshot(s3, "b", "2026-09-22", RECORDS)
    changed = [dict(RECORDS[0], OCCUPIED_ROOMS=11), RECORDS[1]]
    assert save_snapshot(s3, "b", "2026-09-22", changed) is not None
    assert len(s3.objects) == 2


def test_unexpected_s3_error_propagates():
    s3 = FakeS3()
    s3.head_error_code = "403"
    with pytest.raises(ClientError):
        save_snapshot(s3, "b", "2026-09-22", RECORDS)