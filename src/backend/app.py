import os
from functools import lru_cache
from uuid import uuid4

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from flask import Flask, jsonify

app = Flask(__name__, static_url_path="/static")


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify(service="backend", status="ok")


@app.get("/api/items")
def items():
    return jsonify([{"id": 1, "name": "item-one"}, {"id": 2, "name": "item-two"}])


@lru_cache(maxsize=1)
def storage():
    return BlobServiceClient(
        os.environ["AZURE_STORAGE_ACCOUNT_URL"],
        credential=DefaultAzureCredential(),
        connection_timeout=5,
        read_timeout=5,
        retry_total=1,
    ).get_container_client("app-data")


@app.post("/api/storage/test")
def storage_test():
    if not os.environ.get("AZURE_STORAGE_ACCOUNT_URL"):
        return jsonify(error="Storage is not configured"), 503
    try:
        # Independent names prevent concurrent replicas overwriting each other.
        blob = storage().get_blob_client(f"healthchecks/{uuid4().hex}.txt")
        blob.upload_blob(b"blob storage is working", timeout=5)
        try:
            content = blob.download_blob(timeout=5).readall().decode()
        finally:
            blob.delete_blob(timeout=5)
        return jsonify(status="ok", content=content)
    except Exception:
        app.logger.exception("Blob storage check failed")
        return jsonify(error="Blob storage request failed"), 502
