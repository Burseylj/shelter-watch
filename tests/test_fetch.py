import pytest

import fetch
from fetch import calculate_occupancy, get_history


def bed(occupied, capacity):
    return {"CAPACITY_TYPE": "Bed Based Capacity", "OCCUPIED_BEDS": occupied, "CAPACITY_ACTUAL_BED": capacity}


def room(occupied, capacity):
    return {"CAPACITY_TYPE": "Room Based Capacity", "OCCUPIED_ROOMS": occupied, "CAPACITY_ACTUAL_ROOM": capacity}


def test_empty_records_gives_zeros():
    stats = calculate_occupancy([])
    assert stats["bed_occupancy_rate"] == 0
    assert stats["room_occupancy_rate"] == 0


def test_bed_and_room_rows_aggregate_separately():
    stats = calculate_occupancy([bed(40, 50), bed(40, 50), room(45, 50)])
    assert stats["bed_occupied"] == 80
    assert stats["bed_capacity"] == 100
    assert stats["bed_occupancy_rate"] == pytest.approx(80.0)
    assert stats["room_occupancy_rate"] == pytest.approx(90.0)


def test_null_empty_and_string_values_are_handled():
    records = [
        {"CAPACITY_TYPE": "Bed Based Capacity", "OCCUPIED_BEDS": None, "CAPACITY_ACTUAL_BED": 10},
        {"CAPACITY_TYPE": "Bed Based Capacity", "OCCUPIED_BEDS": "", "CAPACITY_ACTUAL_BED": ""},
        bed("5", "10"),
    ]
    stats = calculate_occupancy(records)
    assert stats["bed_occupied"] == 5
    assert stats["bed_capacity"] == 20


def test_zero_capacity_does_not_divide_by_zero():
    stats = calculate_occupancy([bed(5, 0), room(3, 0)])
    assert stats["bed_occupancy_rate"] == 0
    assert stats["room_occupancy_rate"] == 0


class FakeResponse:
    def __init__(self, records):
        self._records = records

    def json(self):
        return {"result": {"records": self._records}}


def stub_get(monkeypatch, records):
    monkeypatch.setattr(fetch.requests, "get", lambda url, params=None: FakeResponse(records))


def test_get_history_groups_by_date_and_returns_n_newest(monkeypatch):
    rows = [  # newest first, as the API returns them
        {"OCCUPANCY_DATE": "2026-09-22", **room(25, 25)},
        {"OCCUPANCY_DATE": "2026-09-22", **room(25, 25)},
        {"OCCUPANCY_DATE": "2026-09-21", **room(25, 50)},
        {"OCCUPANCY_DATE": "2026-09-20", **room(10, 50)},
    ]
    stub_get(monkeypatch, rows)
    history = get_history(days=2)
    assert [d for d, _ in history] == ["2026-09-22", "2026-09-21"]
    assert history[0][1]["room_occupied"] == 50  # both rows for the date summed
    assert history[1][1]["room_occupancy_rate"] == pytest.approx(50.0)


def test_get_history_with_no_records_returns_empty_list(monkeypatch):
    stub_get(monkeypatch, [])
    assert get_history(days=30) == []