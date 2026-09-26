import os
import logging
from datetime import datetime, timezone

from fetch import get_latest_date, get_records_for_date, calculate_occupancy, get_history, OccupancyStats
from post import post_carousel_to_instagram
from render import render_occupancy, render_trend_graph
from upload import upload_image_bucket, get_storage_client
from state import get_last_posted_date, set_last_posted_date
from ig_token import get_ig_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

TREND_HISTORY_DAYS = 30


def build_caption(stats: OccupancyStats, date: str) -> str:
    return (
        f"Toronto shelter occupancy — {date}\n\n"
        f"Beds: {stats['bed_occupied']:.0f}/{stats['bed_capacity']:.0f} "
        f"({stats['bed_occupancy_rate']}%)\n"
        f"Rooms: {stats['room_occupied']:.0f}/{stats['room_capacity']:.0f} "
        f"({stats['room_occupancy_rate']}%)"
    )

def fetch_stage(days: int = TREND_HISTORY_DAYS) -> tuple[OccupancyStats, list[tuple[str, OccupancyStats]]]:
    date = get_latest_date()
    records = get_records_for_date(date)
    stats = calculate_occupancy(records)
    history = get_history(days)
    return stats, history

def render_stage(date: str, stats: OccupancyStats, history: list, run_timestamp: str) -> tuple[str, str]:
    occupancy_path = render_occupancy(stats, date, output_path=f"/tmp/occupancy-{run_timestamp}.png")
    trend_path = render_trend_graph(history, output_path=f"/tmp/trend-{run_timestamp}.png")
    return occupancy_path, trend_path


def upload_stage(occupancy_path: str, trend_path: str, bucket: str, date: str, run_timestamp: str) -> tuple[str, str]:
    occupancy_url = upload_image_bucket(occupancy_path, bucket, f"occupancy-{date}-{run_timestamp}.png")
    trend_url = upload_image_bucket(trend_path, bucket, f"trend-{date}-{run_timestamp}.png")
    return occupancy_url, trend_url


def main() -> None:
    logger.info("Starting shelter occupancy pipeline")
    force_post = os.environ.get("FORCE_POST", "").lower() in ("1", "true", "yes")
    bucket = os.environ["BUCKET_NAME"]
    client = get_storage_client()

    date = get_latest_date()
    last_posted = get_last_posted_date(client, bucket)
    if date == last_posted and not force_post:
        logger.info(f"No new data since last post ({date}) — skipping")
        return
    
    stats, history = fetch_stage()

    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    occupancy_path, trend_path = render_stage(date, stats, history, run_timestamp)
    occupancy_url, trend_url = upload_stage(occupancy_path, trend_path, bucket, date, run_timestamp)

    access_token = get_ig_token(client, bucket)
    caption = build_caption(stats, date)
    post_carousel_to_instagram([occupancy_url, trend_url], caption, access_token)

    set_last_posted_date(client, bucket, date)
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline failed")
        raise