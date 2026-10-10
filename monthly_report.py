import logging
from datetime import datetime, timezone

import config
from ig_token import get_ig_token
from monthly_fetch import (
    RECENT_ROWS_LIMIT,
    MonthReport,
    build_month_report,
    get_recent_rows,
    latest_row_date,
)
from post import post_carousel_to_instagram
from render import (
    change_text,
    month_label,
    percent_change,
    render_month_card,
    render_month_daily_chart,
)
from snapshot import save_snapshot
from state import get_last_posted_month, set_last_posted_month
from upload import get_storage_client, upload_image_bucket

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_caption(report: MonthReport) -> str:
    stats = report["stats"]
    lines = [
        f"Toronto Central Intake — {month_label(stats['month'])}",
        "",
        f"Average unmatched callers per day: {stats['avg_per_day']:.0f}",
    ]
    for other in (report["previous"], report["year_ago"]):
        if other is None:
            continue
        pct = percent_change(stats["avg_per_day"], other["avg_per_day"])
        if pct is not None:
            lines.append(f"{change_text(pct)} vs {month_label(other['month'])}")
    lines += [
        "",
        f"{stats['unmatched']:,} unmatched callers summed across {stats['days']} days. "
        "Counts are daily, so one person can appear on more than one day.",
        "",
        "Swipe for the day-by-day numbers →",
    ]
    return "\n".join(lines)


def ingest_stage(client, bucket: str) -> list[dict]:
    rows = get_recent_rows(RECENT_ROWS_LIMIT)
    save_snapshot(client, bucket, "central-intake-queue", latest_row_date(rows), rows)
    return rows


def render_stage(report: MonthReport, run_timestamp: str) -> tuple[str, str]:
    card_path = render_month_card(report, output_path=f"/tmp/monthly-card-{run_timestamp}.png")
    chart_path = render_month_daily_chart(
        report, output_path=f"/tmp/monthly-daily-{run_timestamp}.png"
    )
    return card_path, chart_path


def upload_stage(
    card_path: str, chart_path: str, bucket: str, month: str, run_timestamp: str
) -> tuple[str, str]:
    card_url = upload_image_bucket(card_path, bucket, f"monthly-card-{month}-{run_timestamp}.png")
    chart_url = upload_image_bucket(
        chart_path, bucket, f"monthly-daily-{month}-{run_timestamp}.png"
    )
    return card_url, chart_url


def main() -> None:
    logger.info("Starting monthly unmatched-callers pipeline")
    bucket = config.bucket_name()
    client = get_storage_client()

    rows = ingest_stage(client, bucket)
    report = build_month_report(rows)
    month = report["stats"]["month"]

    last_posted = get_last_posted_month(client, bucket)
    if month == last_posted and not config.force_post():
        logger.info(f"No new month since last post ({month}) — skipping")
        return

    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    card_path, chart_path = render_stage(report, run_timestamp)
    card_url, chart_url = upload_stage(card_path, chart_path, bucket, month, run_timestamp)

    access_token = get_ig_token(client, bucket)
    caption = build_caption(report)
    post_carousel_to_instagram([card_url, chart_url], caption, access_token)

    set_last_posted_month(client, bucket, month)
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline failed")
        raise