#!/usr/bin/env bash
set -euo pipefail

RG="akspoc-rg"
PREFIX="akspoc"
LOCATION="westus3"
PG_PASS="YourTempPassword123!"
TFSTATE_RG="tfstate-rg"

echo "==> [1/8] Deleting resource group $RG (this can take 5-10 min)..."
az group delete --name "$RG" --yes --no-wait || true

echo "==> [2/8] Waiting for deletion to finish..."
while az group show --name "$RG" &>/dev/null; do sleep 15; done
echo "    RG gone."

echo "==> [3/8] Wiping remote Terraform state blob..."
TFSTATE_SA=$(az storage account list --resource-group "$TFSTATE_RG" --query "[0].name" -o tsv)
az storage blob delete \
  --account-name "$TFSTATE_SA" \
  --container-name tfstate \
  --name aks-poc.tfstate \
  --auth-mode login 2>/dev/null || true
echo "    State wiped from $TFSTATE_SA."

echo "==> [4/8] Terraform init + apply (15-20 min, do not interrupt)..."
cd infrastructure
rm -rf .terraform .terraform.lock.hcl terraform.tfstate terraform.tfstate.backup
terraform init -input=false
terraform apply -auto-approve -input=false -var="postgres_admin_password=$PG_PASS"
cd ..

echo "==> [5/8] Fetching AKS credentials..."
az aks get-credentials --resource-group "$RG" --name "${PREFIX}-aks" --overwrite-existing

echo "==> [6/8] Getting ACR name and building/pushing images..."
ACR=$(cd infrastructure && terraform output -raw acr_login_server 2>/dev/null || true)
if [ -z "$ACR" ]; then
  ACR="$(az acr list --resource-group "$RG" --query '[0].loginServer' -o tsv)"
fi
ACR_NAME="${ACR%%.*}"
echo "    ACR: $ACR"

az acr login --name "$ACR_NAME"
docker build -t "$ACR/backend:v1"  -f src/backend/Dockerfile  src/backend
docker build -t "$ACR/frontend:v1" -f src/frontend/Dockerfile src/frontend
docker push "$ACR/backend:v1"
docker push "$ACR/frontend:v1"

echo "==> [7/8] Rendering k8s manifests with real ACR address..."
sed "s|REPLACE_ACR|$ACR|g" k8s/backend.yaml  > /tmp/backend.rendered.yaml
sed "s|REPLACE_ACR|$ACR|g" k8s/frontend.yaml > /tmp/frontend.rendered.yaml
# If your YAML already contains the hardcoded ACR from earlier, sed is a no-op.

echo "==> [8/8] Applying to AKS and waiting for rollout..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f /tmp/backend.rendered.yaml
kubectl apply -f /tmp/frontend.rendered.yaml
kubectl -n poc-app rollout status deploy/backend  --timeout=180s
kubectl -n poc-app rollout status deploy/frontend --timeout=180s

echo
echo "==================================================="
echo " DONE. Frontend IP:"
kubectl -n poc-app get svc frontend
echo "==================================================="