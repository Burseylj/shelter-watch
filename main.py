import os
import logging
from fetch import get_latest_date, get_records_for_date, calculate_occupancy
from render import render_occupancy
from upload import upload_image
from post import post_to_instagram

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

    records = get_records_for_date(date)
    logger.info(f"Fetched {len(records)} records")

    stats = calculate_occupancy(records)
    logger.info(f"Occupancy calculated: {stats}")

    image_path = render_occupancy(stats, date, output_path="/tmp/occupancy.png")

    bucket = os.environ["BUCKET_NAME"]
    image_url = upload_image(image_path, bucket, f"occupancy-{date}.png")

    caption = build_caption(stats, date)
    result = post_to_instagram(image_url, caption)

    logger.info("Pipeline completed successfully")
    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline failed")
        raise