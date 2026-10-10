import gzip
import hashlib
import json
import logging
from datetime import datetime, timezone

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def save_snapshot(
    client, bucket: str, dataset: str, date: str, records: list[dict]
) -> str | None:
    body = json.dumps(sorted(records, key=lambda r: r["_id"]), sort_keys=True)
    digest = hashlib.sha256(body.encode()).hexdigest()[:12]
    key = f"snapshots/{dataset}/{date}/{digest}.json.gz"

    try:
        client.head_object(Bucket=bucket, Key=key)
        logger.info(f"Snapshot unchanged for {dataset} {date} ({digest})")
        return None
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchKey", "NotFound"):
            raise

    fetched_at = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(
        {"fetched_at": fetched_at, "dataset": dataset, "date": date, "records": json.loads(body)}
    )
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=gzip.compress(payload.encode()),
        ContentType="application/gzip",
    )
    logger.info(f"New snapshot version for {dataset} {date}: {key} ({len(records)} records)")
    return key