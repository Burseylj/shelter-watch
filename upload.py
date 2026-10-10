import logging

import boto3
import requests

import config

logger = logging.getLogger(__name__)


def get_storage_client():
    return boto3.client(
        "s3",
        endpoint_url=config.storage_endpoint_url(),
        aws_access_key_id=config.storage_key_id(),
        aws_secret_access_key=config.storage_secret_key(),
    )


def upload_image_bucket(local_path: str, bucket: str, key: str) -> str:
    logger.info(f"Uploading {local_path} to {bucket}/{key}")
    client = get_storage_client()
    client.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "image/png"})

    url = f"{config.storage_public_url_base()}/{key}"
    logger.info(f"Upload complete: {url}")

    check = requests.head(url, timeout=10)
    if check.status_code != 200:
        logger.error(f"Uploaded but not publicly reachable: {url} ({check.status_code})")
        raise RuntimeError(f"Uploaded but not publicly reachable: {url} ({check.status_code})")

    logger.info("Public reachability confirmed")
    return url