# Run this PoC yourself

## Prerequisites

- Git, Bash, Python 3.11+, Terraform >= 1.7 and < 2, Azure CLI, Docker, kubectl and jq.
- An active Azure subscription with permission to create resources and assign roles
  (Owner, or Contributor plus Role Based Access Control Administrator, scoped as appropriate).
- Docker running with Linux amd64 image support (Docker Desktop supports this).
- A region that supports AKS and the chosen VM size. Defaults are `westus3` and
  `Standard_D2s_v4`. Two nodes need four vCPUs; allow six for a third node or an
  upgrade surge, and eight for a surge at the autoscaler maximum of three nodes.

Commands assume macOS, Linux, or WSL with Bash. Keep the virtual environment
activated: the deployment renderer imports PyYAML. Do not commit `.terraform`,
state, plan files, connection strings, tokens or your own `.tfvars`.

## 1. Clone and test locally

```sh
git clone https://github.com/krishnagmx/azure-aks-poc.git
cd azure-aks-poc
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m flask --app src/backend/app run
```

Open `http://127.0.0.1:5000`, then stop the development server with Ctrl+C.
The mocked tests do not need Azure. `/api/health` does not depend on storage;
`/api/items` returns sample data. `POST /api/storage/test` returns 503 when
`AZURE_STORAGE_ACCOUNT_URL` is unset.

For local real-blob testing, set `AZURE_STORAGE_ACCOUNT_URL` to your account's HTTPS
blob endpoint, sign in with `az login`, and give that local identity Storage Blob
Data Contributor access to the private `app-data` container. The container must
already exist. Do not use the published demo's identity or storage settings.

## 2. Select your Azure subscription

```sh
az login
az account list --query '[].{name:name,id:id,isDefault:isDefault}' -o table
az account set --subscription <your-subscription-id>
az account show --query '{name:name,id:id}' -o table
az vm list-usage --location westus3 -o table
```

Check total regional vCPU quota, DSv4-family quota and VM availability for your
subscription. An allowed SKU does not guarantee regional capacity.

## 3. Bootstrap your remote state

The backend exists separately from the app stack. The script creates a resource
group, an LRS storage account and a private `tfstate` container, enables versioning
and soft deletion, and runs Terraform initialization.

```sh
# Optional overrides; choose your own names if sharing a subscription.
export TFSTATE_RESOURCE_GROUP=tfstate-rg
# export TFSTATE_STORAGE_ACCOUNT=<globally-unique-lowercase-name>
export TFSTATE_LOCATION=westus3
bash scripts/bootstrap-backend.sh
```

If no account name is supplied, it is derived from the active subscription ID.
Record the account name shown in Azure or find it with:

```sh
az storage account list --resource-group "$TFSTATE_RESOURCE_GROUP" --query '[].name' -o tsv
```

The current identity needs permission to list storage account keys. The backend
and Terraform state can contain credentials: restrict access. Do not reuse another
project's state or reconfigure a shared backend to a new subscription casually.

## 4. Review and provision

```sh
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
# Edit location, prefix and node_size for your subscription if necessary.
terraform -chdir=infrastructure fmt -check -recursive
terraform -chdir=infrastructure validate
terraform -chdir=infrastructure plan -out=deployment.tfplan
# Read the plan; proceed only if it describes the resources you intend to create.
terraform -chdir=infrastructure apply deployment.tfplan
terraform -chdir=infrastructure output deployment
```

On a fresh setup the plan creates 10 resources. Provisioning normally involves
waiting for Azure; there is no guaranteed completion time. The app authenticates
with a managed identity federated to `system:serviceaccount:poc-app:app`, scoped to
one blob container. No PostgreSQL password or app storage secret is needed.

**Migration:** this configuration replaced an older modular stack. Resource
addresses changed. Do not apply it against recovered old state without first
reviewing imports/moves and a migration plan.

## 5. Build and deploy

Keep `.venv` activated, verify Docker is running, then:

```sh
IMAGE_TAG="$(git rev-parse --short HEAD)-$(date -u +%Y%m%d%H%M%S)" bash scripts/deploy.sh
kubectl get nodes
kubectl get pods,deployments,services,pdb -n poc-app -o wide
kubectl get service app -n poc-app
```

The script builds one amd64 image, pushes it to your ACR, resolves its digest,
gets AKS credentials, renders non-secret settings from Terraform outputs and waits
for the rollout. It changes your current kubectl context. A newly created public
LoadBalancer IP can remain `<pending>` after pods become Ready; wait until Azure
assigns the address. Permission propagation can also delay initial pulls/blob calls.

## 6. Verify and reproduce the small-load check

Replace the URL with **your own** public service address:

```sh
export APP_URL=http://<your-service-ip>
python scripts/verify.py "$APP_URL"
kubectl top pods -n poc-app
terraform -chdir=infrastructure plan -detailed-exitcode
```

`verify.py` checks the page and items API, creates/reads/deletes three test blobs,
then issues 100 health requests with 10 concurrent workers and prints JSON metrics.
Only run it against a deployment you own. This is a short functional/load sample,
not a stress test; client network and cold-start effects influence results.
Terraform detailed exit codes are 0 for no change, 2 for a diff and 1 for an error.

To reproduce the rolling-update check (this deliberately restarts the app):

```sh
python scripts/verify_rollout.py "$APP_URL"
kubectl get pods -n poc-app -o wide
```

The script monitors public health while `kubectl rollout restart` replaces pods.
Verify the final non-terminating replicas occupy separate nodes. The spread rule
uses `matchLabelKeys: [pod-template-hash]` to keep revisions balanced during updates.
A disruption budget covers voluntary disruptions; these checks do not demonstrate
node failure, zone failure, disaster recovery or an uptime SLA.

## Troubleshooting

| Symptom | Check or action |
| --- | --- |
| `ResourceGroupNotFound` during init | Bootstrap your backend; check subscription and backend names |
| Backend or blob 403 | Check management permissions, data-plane RBAC, current identity and propagation |
| `QuotaExceeded` / node pool create fails | Check both regional and VM-family vCPU quotas; select an available region/size or request quota |
| `ImagePullBackOff` | Check ACR image/digest, kubelet AcrPull assignment and propagation |
| Storage 502 | Inspect `kubectl logs -n poc-app deployment/app`; check service-account client ID, pod identity label, federation subject and blob role |
| `Pending` pod | Inspect `kubectl describe pod -n poc-app <pod>` and node resources; check spread constraints |
| `<pending>` service address | Inspect service events; Azure may still be provisioning the LoadBalancer |
| Metrics unavailable | Allow the metrics server to collect a sample for newly created pods |
| `ModuleNotFoundError: yaml` | Activate `.venv` and install `requirements-dev.txt` |
| Credential/plugin errors in Terraform | Check Azure login, network access, selected subscription and local execution restrictions |

Helpful commands:

```sh
kubectl describe deployment app -n poc-app
kubectl get events -n poc-app --sort-by=.lastTimestamp
kubectl logs -n poc-app deployment/app
kubectl rollout history deployment/app -n poc-app
# If an app revision is bad (does not revert Terraform):
kubectl rollout undo deployment/app -n poc-app
```

## Cleanup

These commands delete the app and provisioned infrastructure. Copy out any data
or evidence you need before running them, and verify your subscription/context.

```sh
# Delete the Service first so Kubernetes can release its managed LoadBalancer resources.
kubectl delete namespace poc-app --wait=true
terraform -chdir=infrastructure plan -destroy -out=destroy.tfplan
# Review the destruction plan, then:
terraform -chdir=infrastructure apply destroy.tfplan
```

The bootstrap backend is intentionally retained. Keep it until destruction finishes
and you no longer need the state/version history. If its resource group is dedicated
to this PoC and you want to remove the backend too, review its contents first, then
run `az group delete --name <your-state-resource-group>`. Do not delete shared state
or unrelated resources. Confirm Azure no longer lists app/node resource groups;
storage retained for state continues to incur charges.
