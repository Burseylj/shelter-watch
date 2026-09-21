# upload.py
import os
import boto3

def get_storage_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )

def upload_image(local_path, bucket, key):
    client = get_storage_client()
    client.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "image/png"})
    return f"{os.environ['R2_PUBLIC_URL_BASE']}/{key}"