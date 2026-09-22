import os
import json
import logging
from datetime import datetime, timezone
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

TOKEN_STATE_KEY = "state/ig-token.json"
GRAPH_URL = os.environ["GRAPH_URL"]
REFRESH_INTERVAL_DAYS = 45  # refresh well ahead of the 60-day hard expiry


def _load_token_state(client, bucket):
    try:
        resp = client.get_object(Bucket=bucket, Key=TOKEN_STATE_KEY)
        return json.loads(resp["Body"].read().decode("utf-8"))
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            logger.info("No stored IG token state found — bootstrapping from env var")
            return None
        raise


def _save_token_state(client, bucket, access_token, refreshed_at):
    body = json.dumps({"access_token": access_token, "refreshed_at": refreshed_at})
    client.put_object(Bucket=bucket, Key=TOKEN_STATE_KEY, Body=body.encode("utf-8"))
    logger.info(f"Saved IG token state (refreshed_at={refreshed_at})")


def _refresh_token(access_token):
    resp = requests.get(
        f"{GRAPH_URL}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": access_token},
    )
    if resp.status_code != 200:
        logger.error(f"Token refresh failed: {resp.status_code} {resp.text}")
        raise RuntimeError(f"Token refresh failed: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


def get_valid_token(client, bucket):
    state = _load_token_state(client, bucket)

    if state is None:
        access_token = os.environ["IG_ACCESS_TOKEN"]
        refreshed_at = datetime.now(timezone.utc).isoformat()
        _save_token_state(client, bucket, access_token, refreshed_at)
        return access_token

    access_token = state["access_token"]
    refreshed_at = datetime.fromisoformat(state["refreshed_at"])
    age_days = (datetime.now(timezone.utc) - refreshed_at).days

    if age_days >= REFRESH_INTERVAL_DAYS:
        logger.info(f"Token is {age_days} days old — refreshing")
        new_token = _refresh_token(access_token)
        _save_token_state(client, bucket, new_token, datetime.now(timezone.utc).isoformat())
        return new_token

    logger.info(f"Token is {age_days} days old — no refresh needed")
    return access_token