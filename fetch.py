import requests

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
RESOURCE_ID = "42714176-4f05-44e6-b157-2b57f29b856a"


def get_latest_date():
    url = BASE_URL + "/api/3/action/datastore_search"
    params = {
        "resource_id": RESOURCE_ID,
        "sort": "OCCUPANCY_DATE desc",
        "limit": 1,
    }
    result = requests.get(url, params=params).json()["result"]
    return result["records"][0]["OCCUPANCY_DATE"]


def get_records_for_date(date):
    url = BASE_URL + "/api/3/action/datastore_search"
    params = {
        "resource_id": RESOURCE_ID,
        "filters": '{"OCCUPANCY_DATE": "%s"}' % date,
        "limit": 5000,
    }
    result = requests.get(url, params=params).json()["result"]
    return result["records"]


def to_number(value):
    if value in (None, ""):
        return 0
    return float(value)


def calculate_occupancy(records):
    bed_occupied = 0
    bed_capacity = 0
    room_occupied = 0
    room_capacity = 0

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