#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${IMAGE_TAG:?Set an immutable image tag, such as the Git commit SHA}"

settings=$(terraform -chdir=infrastructure output -json deployment)
read_setting() { jq -er ".$1" <<< "$settings"; }
registry=$(read_setting registry)
image="$(read_setting image):${IMAGE_TAG}"

az acr login --name "$registry"
docker build --platform linux/amd64 -t "$image" -f src/backend/dockerfile src/backend
docker push "$image"
# Use a digest so reusing a tag cannot silently change the deployed image.
digest=$(az acr repository show --name "$registry" --image "app:${IMAGE_TAG}" --query digest -o tsv)
: "${digest:?ACR did not return an image digest}"
APP_IMAGE="$(read_setting image)@${digest}"
CLIENT_ID=$(read_setting client_id)
STORAGE_URL=$(read_setting storage_url)
export APP_IMAGE CLIENT_ID STORAGE_URL
az aks get-credentials --resource-group "$(read_setting resource_group)" \
  --name "$(read_setting cluster)" --overwrite-existing
kubectl apply -f k8s/namespace.yaml
python3 scripts/render.py | kubectl apply -n poc-app -f -
kubectl rollout status deployment/app -n poc-app --timeout=180s
kubectl get service app -n poc-app
