import os


def graph_url() -> str:
    return os.environ["GRAPH_URL"]


def ig_user_id() -> str:
    return os.environ["IG_USER_ID"]


def ig_access_token() -> str:
    return os.environ["IG_ACCESS_TOKEN"]


def bucket_name() -> str:
    return os.environ["BUCKET_NAME"]


def storage_endpoint_url() -> str:
    return os.environ["STORAGE_ENDPOINT_URL"]


def storage_key_id() -> str:
    return os.environ["STORAGE_KEY_ID"]


def storage_secret_key() -> str:
    return os.environ["STORAGE_SECRET_KEY"]


def storage_public_url_base() -> str:
    return os.environ["STORAGE_PUBLIC_URL_BASE"]


def force_post() -> bool:
    return os.environ.get("FORCE_POST", "").lower() in ("1", "true", "yes")