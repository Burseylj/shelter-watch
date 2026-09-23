import logging
from itertools import groupby, islice
from typing import TypedDict

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
RESOURCE_ID = "42714176-4f05-44e6-b157-2b57f29b856a"

# CKAN datastore_search enforces a server-side cap on `limit` regardless of
# what's requested; stay under it so a large `days` value doesn't silently
# fail instead of just returning fewer dates than asked for.
MAX_DATASTORE_LIMIT = 32000


class OccupancyStats(TypedDict):
    bed_occupied: float
    bed_capacity: float
    bed_occupancy_rate: float
    room_occupied: float
    room_capacity: float
    room_occupancy_rate: float


def get_latest_date() -> str:
    logger.info("Fetching latest occupancy date")
    url = BASE_URL + "/api/3/action/datastore_search"
    params = {
        "resource_id": RESOURCE_ID,
        "sort": "OCCUPANCY_DATE desc",
        "limit": 1,
    }
    result = requests.get(url, params=params).json()["result"]
    date = result["records"][0]["OCCUPANCY_DATE"]
    logger.info(f"Latest occupancy date: {date}")
    return date


def get_records_for_date(date: str) -> list[dict]:
    logger.info(f"Fetching records for {date}")
    url = BASE_URL + "/api/3/action/datastore_search"
    params = {
        "resource_id": RESOURCE_ID,
        "filters": '{"OCCUPANCY_DATE": "%s"}' % date,
        "limit": 5000,
    }
    result = requests.get(url, params=params).json()["result"]
    records = result["records"]
    logger.info(f"Fetched {len(records)} records for {date}")
    return records


def get_history(days: int = 30) -> list[tuple[str, OccupancyStats]]:
    logger.info(f"Fetching occupancy history for the last {days} days")

    url = BASE_URL + "/api/3/action/datastore_search"
    params: dict[str, str | int] = {
        "resource_id": RESOURCE_ID,
        "sort": "OCCUPANCY_DATE desc",
        "limit": min(200 * days, MAX_DATASTORE_LIMIT),
    }
    result = requests.get(url, params=params).json()["result"]
    records = result["records"]

    grouped = groupby(records, key=lambda r: r["OCCUPANCY_DATE"])
    history = [
        (date, calculate_occupancy(list(recs))) for date, recs in islice(grouped, days)
    ]

    if len(history) < days:
        logger.warning(
            f"Requested {days} days of history but only found {len(history)} — "
            f"the record limit may be too small, or the dataset doesn't go back that far"
        )

    logger.info(f"Built history with {len(history)} data points")
    rates = [stats["room_occupancy_rate"] for _, stats in history]
    logger.info(f"History room occupancy rate range: {min(rates):.1f}%–{max(rates):.1f}% across {len(history)} days")
    return history


def to_number(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def calculate_occupancy(records: list[dict]) -> OccupancyStats:
    bed_occupied = 0.0
    bed_capacity = 0.0
    room_occupied = 0.0
    room_capacity = 0.0

    for r in records:
        if r.get("CAPACITY_TYPE") == "Bed Based Capacity":
            bed_occupied += to_number(r.get("OCCUPIED_BEDS"))
            bed_capacity += to_number(r.get("CAPACITY_ACTUAL_BED"))
        elif r.get("CAPACITY_TYPE") == "Room Based Capacity":
            room_occupied += to_number(r.get("OCCUPIED_ROOMS"))
            room_capacity += to_number(r.get("CAPACITY_ACTUAL_ROOM"))

    bed_rate = (bed_occupied / bed_capacity * 100) if bed_capacity else 0
    room_rate = (room_occupied / room_capacity * 100) if room_capacity else 0

    return {
        "bed_occupied": bed_occupied,
        "bed_capacity": bed_capacity,
        "bed_occupancy_rate": round(bed_rate, 2),
        "room_occupied": room_occupied,
        "room_capacity": room_capacity,
        "room_occupancy_rate": round(room_rate, 2),
    }