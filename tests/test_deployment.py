import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("render", ROOT / "scripts/render.py")
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class DeploymentTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "CLIENT_ID": "test-client",
        "STORAGE_URL": "https://test.blob.core.windows.net/",
        "APP_IMAGE": "test.azurecr.io/app@sha256:123",
    })
    def test_render_is_valid_and_wires_identity_and_image(self):
        documents = list(yaml.safe_load_all(yaml.safe_dump_all(render.manifests())))
        by_kind = {document["kind"]: document for document in documents}
        account = by_kind["ServiceAccount"]
        deployment = by_kind["Deployment"]
        pod = deployment["spec"]["template"]
        container = pod["spec"]["containers"][0]
        self.assertEqual(account["metadata"]["annotations"]["azure.workload.identity/client-id"], "test-client")
        self.assertEqual(pod["spec"]["serviceAccountName"], account["metadata"]["name"])
        self.assertEqual(pod["metadata"]["labels"]["azure.workload.identity/use"], "true")
        self.assertEqual(container["image"], "test.azurecr.io/app@sha256:123")
        self.assertEqual(container["env"][0]["value"], "https://test.blob.core.windows.net/")
        for key, value in by_kind["Service"]["spec"]["selector"].items():
            self.assertEqual(pod["metadata"]["labels"][key], value)

    @patch.dict(os.environ, {}, clear=True)
    def test_render_requires_configuration(self):
        with self.assertRaises(KeyError):
            render.manifests()
