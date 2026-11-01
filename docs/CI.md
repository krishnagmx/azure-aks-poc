# GitHub Actions: validation first, deployment opt-in

The workflow runs tests, Terraform formatting/validation, shell syntax checks and
a Docker build for pushes and pull requests. Infrastructure is not applied by CI.
The deploy job is enabled only when `AZURE_DEPLOY_ENABLED` is `true`, on main-branch
pushes or manual runs, after the check job succeeds.

## Repository variables

| Variable | Required value |
| --- | --- |
| `AZURE_DEPLOY_ENABLED` | `true` only after the remaining setup is complete |
| `AZURE_CLIENT_ID` | Client ID of your deployment app registration or managed identity |
| `AZURE_TENANT_ID` | Your Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your target subscription |
| `TFSTATE_STORAGE_ACCOUNT` | Your bootstrap backend account |
| `TFSTATE_RESOURCE_GROUP` | Optional; defaults to `tfstate-rg` |

Add these in GitHub repository **Settings → Secrets and variables → Actions → Variables**.
These are identifiers, not client secrets. Never paste storage keys into variables.

## Federated login

Create a deployment identity in your tenant and configure a federated credential:

```json
{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:OWNER/REPO:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}
```

Replace `OWNER/REPO` with your own fork. Add the federated credential to the actual
app registration (or user-assigned managed identity) whose client ID you configured.
The workflow uses `azure/login` OIDC, not `AZURE_CREDENTIALS` or a storage secret.
See [Azure Login's OIDC instructions](https://github.com/Azure/login#login-with-openid-connect-oidc-recommended).

## Permissions for the deployment identity

Scope permissions to your resources. In this PoC's default AKS configuration,
Azure's cluster-user credential command returns a local kubeconfig credential;
it is sensitive. A production follow-up should configure Entra/Kubernetes RBAC
and least-privilege namespace access deliberately.

| Resource | Required operation / typical role |
| --- | --- |
| Your ACR | Push images (`AcrPush`) |
| Your AKS | Get user credentials (`Azure Kubernetes Service Cluster User Role`) |
| Your backend storage account | Read account metadata and list keys (e.g. Reader plus Storage Account Key Operator Service Role) |

The app's blob identity and the CI identity serve different purposes. Terraform
creates the app identity automatically; it does not create your GitHub deployment
identity or configure your GitHub repository variables.

Provision infrastructure locally following [SETUP.md](SETUP.md), confirm all access,
then set `AZURE_DEPLOY_ENABLED=true` and run the workflow manually from **Actions**.
Inspect the actual run before describing CI deployment as verified. Keep deployment
disabled in forks that only need validation.
