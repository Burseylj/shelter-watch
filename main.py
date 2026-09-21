import os
from fetch import get_latest_date, get_records_for_date, calculate_occupancy
from render import render_occupancy
from upload import upload_image


def main():
    date = get_latest_date()
    records = get_records_for_date(date)
    stats = calculate_occupancy(records)

    image_path = render_occupancy(stats, date, output_path="/tmp/occupancy.png")

    bucket = os.environ["BUCKET_NAME"]
    url = upload_image(image_path, bucket, f"occupancy-{date}.png")

    print(f"Uploaded: {url}")


if __name__ == "__main__":
    main()