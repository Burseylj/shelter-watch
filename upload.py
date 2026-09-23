import os
import logging
import boto3
import requests

logger = logging.getLogger(__name__)


def get_storage_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["STORAGE_ENDPOINT_URL"],
        aws_access_key_id=os.environ["STORAGE_KEY_ID"],
        aws_secret_access_key=os.environ["STORAGE_SECRET_KEY"],
    )


def upload_image_bucket(local_path, bucket, key):
    logger.info(f"Uploading {local_path} to {bucket}/{key}")
    client = get_storage_client()
    client.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "image/png"})

    url = f"{os.environ['STORAGE_PUBLIC_URL_BASE']}/{key}"
    logger.info(f"Upload complete: {url}")

    check = requests.head(url, timeout=10)
    if check.status_code != 200:
        logger.error(f"Uploaded but not publicly reachable: {url} ({check.status_code})")
        raise RuntimeError(f"Uploaded but not publicly reachable: {url} ({check.status_code})")

    logger.info("Public reachability confirmed")
    return url