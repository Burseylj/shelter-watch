import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

IG_USER_ID = os.environ["IG_USER_ID"]
GRAPH_URL = os.environ["GRAPH_URL"]


def _fail(message: str) -> None:
    logger.error(message)
    raise RuntimeError(message)


def _wait_until_finished(access_token: str, creation_id: str, label: str = "Container") -> None:
    for attempt in range(1, 11):
        status_resp = requests.get(
            f"{GRAPH_URL}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token},
        )
        status = status_resp.json().get("status_code")
        logger.info(f"{label} poll {attempt}/10: status={status}")

        if status == "FINISHED":
            return
        if status == "ERROR":
            _fail(f"{label} failed to process: {status_resp.json()}")
        time.sleep(3)

    _fail(f"{label} never finished processing")


def publish_container(access_token: str, creation_id: str) -> dict:
    _wait_until_finished(access_token, creation_id, label="Container")

    logger.info("Publishing container")
    publish_resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
    )
    if publish_resp.status_code != 200:
        _fail(f"Publish failed: {publish_resp.status_code} {publish_resp.text}")

    result = publish_resp.json()
    logger.info(f"Published: {result}")
    return result


def post_to_instagram(image_url: str, caption: str, access_token: str) -> dict:
    # Create media container
    logger.info(f"Creating media container for {image_url}")
    container_resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
    )
    if container_resp.status_code != 200:
        _fail(f"Container creation failed: {container_resp.status_code} {container_resp.text}")

    creation_id = container_resp.json()["id"]
    logger.info(f"Container created: {creation_id}")

    # Publish container
    return publish_container(access_token, creation_id)


def post_carousel_to_instagram(image_urls: list[str], caption: str, access_token: str) -> dict:
    logger.info("Posting carousel")
    image_container_ids = []

    # Create individual image containers
    for image_url in image_urls:
        logger.info(f"Creating media container for {image_url}")
        container_resp = requests.post(
            f"{GRAPH_URL}/{IG_USER_ID}/media",
            data={"image_url": image_url, "is_carousel_item": "true", "access_token": access_token},
        )
        if container_resp.status_code != 200:
            _fail(f"Child container creation failed: {container_resp.status_code} {container_resp.text}")

        creation_id = container_resp.json()["id"]
        _wait_until_finished(access_token, creation_id, label=f"Child container {creation_id}")
        image_container_ids.append(creation_id)
        logger.info(f"Child container ready: {creation_id}")

    # Create parent container for post
    container_resp = requests.post(
        f"{GRAPH_URL}/{IG_USER_ID}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(image_container_ids),
            "caption": caption,
            "access_token": access_token,
        },
    )
    if container_resp.status_code != 200:
        _fail(f"Parent container creation failed: {container_resp.status_code} {container_resp.text}")

    creation_id = container_resp.json()["id"]
    logger.info(f"Parent container created: {creation_id}")

    # Publish container
    return publish_container(access_token, creation_id)