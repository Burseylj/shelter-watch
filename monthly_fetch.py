import logging
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from typing import TypedDict

import requests

from fetch import BASE_URL, to_number

logger = logging.getLogger(__name__)

SERVICE_QUEUE_RESOURCE_ID = "61191143-8143-4425-bf89-2c1523961227"
LOOKBACK_MONTHS = 13 
RECENT_ROWS_LIMIT = 31 * (LOOKBACK_MONTHS + 1)

class MonthStats(TypedDict):
    month: str  # "2026-08"
    days: int
    unmatched: int
    single_call: int
    avg_per_day: float

class MonthReport(TypedDict):
    stats: MonthStats
    previous: MonthStats | None
    year_ago: MonthStats | None
    daily: list[tuple[str, int]]  # (date, unmatched), oldest first

def get_recent_rows(limit: int) -> list[dict]:
    logger.info(f"Fetching last {limit} days of service queue data")
    url = BASE_URL + "/api/3/action/datastore_search"
    params = {"resource_id": SERVICE_QUEUE_RESOURCE_ID, "sort": "Date desc", "limit": limit}
    records = requests.get(url, params=params, timeout=30).json()["result"]["records"]
    logger.info(f"Fetched {len(records)} rows")
    return records

def latest_row_date(rows: list[dict]) -> str:
    if not rows:
        raise ValueError("Service queue returned no rows")
    return max(r["Date"][:10] for r in rows)

def latest_complete_month(last_date: date) -> str:
    last_day = monthrange(last_date.year, last_date.month)[1]
    if last_date.day == last_day:
        return last_date.strftime("%Y-%m")
    previous_month_end = last_date.replace(day=1) - timedelta(days=1)
    return previous_month_end.strftime("%Y-%m")

def shift_month(month: str, delta: int) -> str:
    year, m = (int(p) for p in month.split("-"))
    index = year * 12 + (m - 1) + delta
    return f"{index // 12}-{index % 12 + 1:02d}"

def expected_days(month: str) -> int:
    year, m = (int(p) for p in month.split("-"))
    return monthrange(year, m)[1]

def summarize_month(month: str, rows: list[dict]) -> MonthStats:
    unmatched = sum(int(to_number(r.get("Unmatched callers"))) for r in rows)
    single = sum(int(to_number(r.get("Single call"))) for r in rows)
    days = len(rows)
    return {
        "month": month,
        "days": days,
        "unmatched": unmatched,
        "single_call": single,
        "avg_per_day": round(unmatched / days, 1) if days else 0.0,
    }

def latest_row_date(rows: list[dict]) -> str:
    if not rows:
        raise ValueError("Service queue returned no rows")
    return max(r["Date"][:10] for r in rows)

def build_month_report(rows: list[dict]) -> MonthReport:
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_month[r["Date"][:7]].append(r)

    last_date = date.fromisoformat(latest_row_date(rows))
    month = latest_complete_month(last_date)
    if month not in by_month:
        raise ValueError(f"No rows found for report month {month}")

    def comparison(m: str) -> MonthStats | None:
        if m not in by_month or len(by_month[m]) != expected_days(m):
            logger.info(f"No complete data for comparison month {m}")
            return None
        return summarize_month(m, by_month[m])

    stats = summarize_month(month, by_month[month])
    if stats["days"] != expected_days(month):
        logger.warning(f"{month} has {stats['days']} days of data, expected {expected_days(month)}")

    daily = sorted(
        (r["Date"][:10], int(to_number(r.get("Unmatched callers")))) for r in by_month[month]
    )
    logger.info(f"Report month {month}: {stats['avg_per_day']} unmatched/day over {stats['days']} days")
    return {
        "stats": stats,
        "previous": comparison(shift_month(month, -1)),
        "year_ago": comparison(shift_month(month, -12)),
        "daily": daily,
    }

def get_month_report() -> MonthReport:
    return build_month_report(get_recent_rows(RECENT_ROWS_LIMIT))