import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

IG_USER_ID = os.environ["IG_USER_ID"]
GRAPH_URL = os.environ["GRAPH_URL"]


def post_to_instagram(image_url, caption, access_token):
    logger.info(f"Creating media container for {image_url}")
    container_resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
    )
    if container_resp.status_code != 200:
        logger.error(f"Container creation failed: {container_resp.status_code} {container_resp.text}")
        raise RuntimeError(f"Container creation failed: {container_resp.status_code} {container_resp.text}")

    creation_id = container_resp.json()["id"]
    logger.info(f"Container created: {creation_id}")

    for attempt in range(1, 11):
        status_resp = requests.get(
            f"{GRAPH_URL}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token},
        )
        status = status_resp.json().get("status_code")
        logger.info(f"Poll {attempt}/10: status={status}")

        if status == "FINISHED":
            break
        if status == "ERROR":
            logger.error(f"Instagram failed to process the image: {status_resp.json()}")
            raise RuntimeError(f"Instagram failed to process the image: {status_resp.json()}")
        time.sleep(3)
    else:
        logger.error("Instagram container never finished processing")
        raise RuntimeError("Instagram container never finished processing")

    logger.info("Publishing container")
    publish_resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
    )
    if publish_resp.status_code != 200:
        logger.error(f"Publish failed: {publish_resp.status_code} {publish_resp.text}")
        raise RuntimeError(f"Publish failed: {publish_resp.status_code} {publish_resp.text}")

    result = publish_resp.json()
    logger.info(f"Published: {result}")
    return result