import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

STATE_KEY = "state/last-posted-date.txt"


def get_last_posted_date(client, bucket):
    try:
        resp = client.get_object(Bucket=bucket, Key=STATE_KEY)
        return resp["Body"].read().decode("utf-8").strip()
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            logger.info("No state file found — treating as first run")
            return None
        raise


def set_last_posted_date(client, bucket, date):
    client.put_object(Bucket=bucket, Key=STATE_KEY, Body=date.encode("utf-8"))
    logger.info(f"Updated last-posted-date state to {date}")