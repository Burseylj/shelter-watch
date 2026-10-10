from datetime import date

import pytest

import monthly_fetch
from monthly_fetch import get_month_report, latest_complete_month, shift_month, summarize_month


@pytest.mark.parametrize("last_date, expected", [
    (date(2026, 8, 31), "2026-08"),  # data ends on month end: that month is complete
    (date(2026, 9, 5), "2026-08"),   # mid-month: previous month
    (date(2026, 1, 10), "2025-12"),  # year rollover
])
def test_latest_complete_month(last_date, expected):
    assert latest_complete_month(last_date) == expected


@pytest.mark.parametrize("month, delta, expected", [
    ("2026-08", -1, "2026-07"),
    ("2026-01", -1, "2025-12"),
    ("2026-08", -12, "2025-08"),
])
def test_shift_month(month, delta, expected):
    assert shift_month(month, delta) == expected


def test_summarize_month_handles_nulls():
    rows = [
        {"Unmatched callers": 10, "Single call": 6, "Repeat caller": 4},
        {"Unmatched callers": 10, "Single call": None, "Repeat caller": 4},
    ]
    stats = summarize_month("2026-08", rows)
    assert stats["unmatched"] == 20
    assert stats["single_call"] == 6
    assert stats["avg_per_day"] == 10.0


class FakeResponse:
    def __init__(self, records):
        self._records = records

    def json(self):
        return {"result": {"records": self._records}}


def rows_for(year, month, days, unmatched=10):
    return [
        {
            "Date": f"{year}-{month:02d}-{d:02d}",
            "Unmatched callers": unmatched,
            "Single call": unmatched // 2,
            "Repeat caller": unmatched - unmatched // 2,
        }
        for d in range(days, 0, -1)
    ]


def stub_rows(monkeypatch, rows):
    monkeypatch.setattr(
        monthly_fetch.requests, "get", lambda url, params=None, timeout=None: FakeResponse(rows)
    )


def test_report_uses_latest_complete_month_with_comparisons(monkeypatch):
    rows = (
        rows_for(2026, 9, 5)                # partial month, ignored
        + rows_for(2026, 8, 31, unmatched=10)
        + rows_for(2026, 7, 31, unmatched=8)
        + rows_for(2025, 8, 31, unmatched=20)
    )
    stub_rows(monkeypatch, rows)
    report = get_month_report()
    assert report["stats"]["month"] == "2026-08"
    assert report["stats"]["avg_per_day"] == 10.0
    assert report["previous"]["avg_per_day"] == 8.0
    assert report["year_ago"]["avg_per_day"] == 20.0
    assert len(report["daily"]) == 31
    assert report["daily"][0][0] == "2026-08-01"  # oldest first


def test_report_comparisons_are_none_when_missing(monkeypatch):
    stub_rows(monkeypatch, rows_for(2026, 9, 5) + rows_for(2026, 8, 31))
    report = get_month_report()
    assert report["previous"] is None
    assert report["year_ago"] is None