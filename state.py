import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

LAST_POSTED_DATE_KEY = "state/last-posted-date.txt"
LAST_POSTED_MONTH_KEY = "state/last-posted-month.txt"


def _read_state(client, bucket: str, key: str) -> str | None:
    try:
        resp = client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8").strip()
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            logger.info(f"No state file at {key} — treating as first run")
            return None
        raise


def _write_state(client, bucket: str, key: str, value: str) -> None:
    client.put_object(Bucket=bucket, Key=key, Body=value.encode("utf-8"))
    logger.info(f"Updated {key} to {value}")


def get_last_posted_date(client, bucket: str) -> str | None:
    return _read_state(client, bucket, LAST_POSTED_DATE_KEY)


def set_last_posted_date(client, bucket: str, date: str) -> None:
    _write_state(client, bucket, LAST_POSTED_DATE_KEY, date)


def get_last_posted_month(client, bucket: str) -> str | None:
    return _read_state(client, bucket, LAST_POSTED_MONTH_KEY)


def set_last_posted_month(client, bucket: str, month: str) -> None:
    _write_state(client, bucket, LAST_POSTED_MONTH_KEY, month)