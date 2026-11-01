"""Render non-secret deployment settings without requiring Azure access."""
import os
from pathlib import Path

import yaml


def manifests():
    source = Path(__file__).resolve().parents[1] / "k8s/app.yaml"
    documents = list(yaml.safe_load_all(source.read_text()))
    by_kind = {document["kind"]: document for document in documents}
    by_kind["ServiceAccount"]["metadata"]["annotations"]["azure.workload.identity/client-id"] = os.environ["CLIENT_ID"]
    container = by_kind["Deployment"]["spec"]["template"]["spec"]["containers"][0]
    container["image"] = os.environ["APP_IMAGE"]
    container["env"][0]["value"] = os.environ["STORAGE_URL"]
    return documents


if __name__ == "__main__":
    print(yaml.safe_dump_all(manifests(), sort_keys=False))
