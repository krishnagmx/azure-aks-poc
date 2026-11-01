#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

subscription=$(az account show --query id -o tsv)
compact=${subscription//-/}
state_group=${TFSTATE_RESOURCE_GROUP:-tfstate-rg}
state_account=${TFSTATE_STORAGE_ACCOUNT:-tf${compact:0:17}state}
state_location=${TFSTATE_LOCATION:-westus3}

az account show --query '{subscription:name,id:id}' -o json
az group create --name "$state_group" --location "$state_location" --output none
az storage account create --name "$state_account" --resource-group "$state_group" \
  --location "$state_location" --sku Standard_LRS --kind StorageV2 \
  --min-tls-version TLS1_2 --allow-blob-public-access false --output none
az storage container create --account-name "$state_account" \
  --name tfstate --public-access off --output none
az storage account blob-service-properties update --account-name "$state_account" \
  --resource-group "$state_group" --enable-versioning true \
  --enable-delete-retention true --delete-retention-days 7 --output none
terraform -chdir=infrastructure init -reconfigure \
  -backend-config="resource_group_name=$state_group" \
  -backend-config="storage_account_name=$state_account"
