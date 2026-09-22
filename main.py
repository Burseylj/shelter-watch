import os
import logging
from datetime import datetime, timezone
from fetch import get_latest_date, get_records_for_date, calculate_occupancy
from render import render_occupancy
from upload import upload_image, get_storage_client
from post import post_to_instagram
from state import get_last_posted_date, set_last_posted_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_caption(stats, date):
    return (
        f"Toronto shelter occupancy — {date}\n\n"
        f"Beds: {stats['bed_occupied']:.0f}/{stats['bed_capacity']:.0f} "
        f"({stats['bed_occupancy_rate']}%)\n"
        f"Rooms: {stats['room_occupied']:.0f}/{stats['room_capacity']:.0f} "
        f"({stats['room_occupancy_rate']}%)"
    )


def main():
    logger.info("Starting shelter occupancy pipeline")

    date = get_latest_date()
    logger.info(f"Latest occupancy date: {date}")

    bucket = os.environ["BUCKET_NAME"]
    client = get_storage_client()

    last_posted = get_last_posted_date(client, bucket)
    if date == last_posted:
        logger.info(f"No new data since last post ({date}) — skipping")
        return

    records = get_records_for_date(date)
    logger.info(f"Fetched {len(records)} records")

    stats = calculate_occupancy(records)
    logger.info(f"Occupancy calculated: {stats}")

    image_path = render_occupancy(stats, date, output_path="/tmp/occupancy.png")

    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"occupancy-{date}-{run_timestamp}.png"
    image_url = upload_image(image_path, bucket, key)

    caption = build_caption(stats, date)
    post_to_instagram(image_url, caption)

    set_last_posted_date(client, bucket, date)
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline failed")
        raise