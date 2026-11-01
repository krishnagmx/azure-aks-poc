"""Build project documentation from repository sources and saved evidence.
Requires Pillow (the existing .venv supplies it) and LibreOffice for ODT export.
"""
from pathlib import Path
from html import escape
import json, textwrap
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/documentation-assets'
OUT.mkdir(exist_ok=True)
E = ROOT/'evidence/live-2026-11-01'

def font(n, mono=False):
    p = '/System/Library/Fonts/Menlo.ttc' if mono else '/System/Library/Fonts/Supplemental/Arial.ttf'
    return ImageFont.truetype(p,n)

def capture(name, filename):
    lines=[]
    for line in (E/filename).read_text().splitlines():
        lines.extend(textwrap.wrap(line, 105, replace_whitespace=False, drop_whitespace=False) or [''])
    im=Image.new('RGB',(1600,110+len(lines)*26),'#142139'); d=ImageDraw.Draw(im)
    d.text((30,20),'SAVED EVIDENCE  |  '+filename,font=font(24),fill='#69dfc3')
    for i,line in enumerate(lines): d.text((30,78+i*26),line,font=font(22,True),fill='#f1f5fa')
    im.save(OUT/name)

def flow(name, title, boxes, footer):
    im=Image.new('RGB',(1500,180+len(boxes)*135),'#f2f5fa');d=ImageDraw.Draw(im)
    d.text((45,30),title,font=font(35),fill='#153254')
    for i,(heading,detail) in enumerate(boxes):
        y=100+i*135
        d.rounded_rectangle((80,y,1420,y+95),18,fill='white',outline='#2576bc',width=3)
        d.text((110,y+12),heading,font=font(28),fill='#153254')
        d.text((110,y+51),detail,font=font(23),fill='#43566b')
        if i<len(boxes)-1:
            d.line((750,y+97,750,y+131),fill='#2576bc',width=4)
            d.polygon([(750,y+132),(740,y+117),(760,y+117)],fill='#2576bc')
    d.text((45,125+len(boxes)*135),footer,font=font(21),fill='#43566b')
    im.save(OUT/name)

flow('runtime.png','Runtime request flow',[
('Browser / verification client','HTTP port 80 to the recorded public Service address'),
('Azure LoadBalancer → Kubernetes Service app','Namespace poc-app; Service routes to Ready endpoints on port 8080'),
('AKS node A: app replica 1  |  AKS node B: app replica 2','One Flask/Gunicorn image; health probes; revision-aware topology spreading'),
('Routes: /  |  /api/health  |  /api/items','Page and sample API are served directly by the same application'),
('POST /api/storage/test → Azure Blob Storage','Upload → download → delete a unique healthchecks/*.txt blob in app-data')],
'ACR supplies the digest-pinned image to both replicas using the kubelet AcrPull role.')
flow('identity.png','Storage authentication and authorization flow',[
('Pod uses ServiceAccount poc-app/app','Pod label enables the AKS workload identity integration'),
('AKS OIDC service-account token → Microsoft Entra token exchange','Federation subject: system:serviceaccount:poc-app:app'),
('User-assigned identity akspoc-app','DefaultAzureCredential obtains an Azure access token in the workload'),
('Storage Blob Data Contributor role → private app-data container','Role is scoped to the container; the app uses no storage connection string')],
'Private container means anonymous blob access is disabled; it does not establish private-endpoint networking.')
flow('delivery.png','Provisioning and application delivery flow',[
('Bootstrap backend → Terraform plan / review / apply','Separate state storage; application root creates 10 Terraform resources'),
('Terraform outputs → scripts/deploy.sh','Read registry, cluster, image path, storage URL and workload identity client ID'),
('Build Linux amd64 image → push ACR → resolve digest','Immutable deployment reference: registry/app@sha256:...'),
('Get AKS credentials → render manifests → kubectl apply','Namespace, service account, Deployment, LoadBalancer Service and PDB'),
('Rollout wait → functional / blob / health / placement checks','CI validation runs first; cloud deployment is opt-in and does not apply Terraform')],
'GitHub deployment uses its own OIDC identity, separate from the application blob identity.')
for name,src in [('steady.png','steady-check.json'),('initial.png','initial-check.json'),('rollout.png','rollout.json'),('workloads.png','workloads.txt'),('resources.png','resources.txt'),('plan.png','terraform-plan.txt')]: capture(name,src)

pages=[]
def p(t): return '<p>'+escape(t)+'</p>'
def code(t): return '<pre>'+escape(t)+'</pre>'
def image(n,caption,width=640): return f'<p><img src="{"documentation-assets/"+n}" width="{width}"></p><p class="caption">{escape(caption)}</p>'
def page(title,*body): pages.append('<section><h1>'+title+'</h1>'+''.join(body)+'</section>')
def table(rows): return '<table>'+''.join('<tr>'+''.join('<td>'+escape(str(c))+'</td>' for c in row)+'</tr>' for row in rows)+'</table>'
page('Azure AKS PoC',p('Project architecture, implementation and verification'),p('Technical project documentation • 1 November 2026'),p('Repository: github.com/krishnagmx/azure-aks-poc'),p('A Terraform-managed Azure Kubernetes demonstration with one Python application image, two replicas, Azure Container Registry and identity-based Azure Blob Storage access.'),p('This document describes the committed implementation and the evidence recorded on 1 November 2026. It does not assert that the cloud deployment is currently running.'),p('Contents: 1. Scope and components; 2. Runtime architecture; 3. Identity; 4. Delivery; 5. Application and Kubernetes; 6. Setup and operations; 7. Public verification; 8. Rollout verification; 9. Infrastructure evidence; 10. Limitations and source index.'),p('Evidence images are faithful text renderings of saved JSON and command-output files. They are not original terminal captures, Azure Portal screenshots or new live checks. Architecture diagrams explain the source configuration.'))
page('1. Scope and components',p('The project simplifies an earlier stack to the services the application actually uses. The Node proxy, PostgreSQL, Key Vault and Application Gateway/WAF are outside the current implementation. Earlier evidence in the top-level evidence folder must not be mixed with the dated current-stack evidence.'),table([
('Component','Implementation / purpose'),('Application','Flask + Gunicorn; Python 3.11 slim image; page and API in one container'),('AKS','Free tier; Azure CNI overlay; 2–3 autoscaled Standard_D2s_v4 nodes by default'),('ACR','Basic tier; admin credentials disabled; kubelet AcrPull role'),('Storage','Standard LRS; TLS 1.2 minimum; private app-data container; 7-day blob deletion retention'),('Identity','User-assigned app identity, AKS OIDC federation and container-scoped blob role'),('Networking','Public LoadBalancer Service, HTTP 80 → application 8080'),('State','Separate bootstrap storage backend with versioning and soft deletion')]),p('Default location: westus3. Default naming prefix: akspoc, with a generated suffix for globally unique names. Terraform manages ten resources including the random suffix and role assignments; the backend and Kubernetes objects are managed separately.'))
page('2. Runtime architecture',image('runtime.png','Figure 1. Request and image distribution flow.',620),p('Only the explicit storage-test route calls Blob Storage. Health checks remain independent of storage, so a storage outage does not itself trigger liveness-driven app restarts. The items API returns fixed sample data and has no database dependency.'))
page('3. Workload identity',image('identity.png','Figure 2. Application token and authorization flow.',620),p('The service-account annotation is rendered with the Terraform identity client ID; the pod label azure.workload.identity/use is true. The federated credential trusts the AKS issuer and the AzureADTokenExchange audience.'),p('Application authentication avoids an app storage secret. Terraform backend/provider administration still uses storage keys. The CI deployment identity is separate and must be configured manually with the appropriate registry, AKS and backend permissions.'))
page('4. Provisioning and delivery',image('delivery.png','Figure 3. Local delivery pipeline and verification gates.',620),p('GitHub Actions checks unit tests, Terraform formatting/validation, shell syntax and Docker build on pull requests and main pushes. Deployment requires AZURE_DEPLOY_ENABLED=true, a non-PR main ref, a successful check job and configured OIDC variables. A committed workflow is not evidence of a successful hosted CI run.'))
page('5. Application and Kubernetes',table([('Route','Behavior'),('GET /','Static HTML page'),('GET /api/health','JSON service=backend, status=ok'),('GET /api/items','Two fixed sample items'),('POST /api/storage/test','Unique blob upload/read/delete; 503 if unconfigured; 502 on storage failure')]),p('Gunicorn runs two workers with two threads each on port 8080, a 60-second timeout and a 25-second graceful timeout. The container runs as UID/GID 10001 with a read-only root filesystem, dropped Linux capabilities, no privilege escalation and RuntimeDefault seccomp. A 64 MiB emptyDir supplies writable /tmp.'),table([('Deployment setting','Configured value'),('Replicas / update strategy','2; maxUnavailable=0; maxSurge=1 pod'),('CPU request / limit','100m / 1 CPU per pod'),('Memory request / limit','128 MiB / 256 MiB per pod'),('Termination','35-second grace; 5-second preStop sleep'),('Startup probe','Every 2s; failure threshold 30; timeout 3s'),('Readiness / liveness','Every 5s / 10s; timeout 3s'),('PDB','minAvailable=1 for voluntary disruptions'),('Topology spread','Hostname maxSkew=1; DoNotSchedule; matchLabelKeys=[pod-template-hash]')]),p('The application pod surge and AKS node upgrade surge are separate settings. Neither guarantees extra node capacity when the subscription quota is exhausted.'))
page('6. Deploy from scratch',p('Prerequisites: Python 3.11+, Bash, Git, Terraform >=1.7 and <2, Azure CLI, Docker with Linux amd64 support, kubectl and jq. Azure provisioning needs resource creation and role-assignment permissions. These are documented reproduction steps; this document build does not execute them.'),code('python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements-dev.txt\npython -m unittest discover -s tests -v\npython -m flask --app src/backend/app run'),p('After Azure login, select the intended subscription and check regional and VM-family quota. Bootstrap dedicated state, copy the example Terraform variables and review the plan before applying.'),code('bash scripts/bootstrap-backend.sh\ncp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars\nterraform -chdir=infrastructure init\nterraform -chdir=infrastructure plan -out=deployment.tfplan\nterraform -chdir=infrastructure apply deployment.tfplan\nIMAGE_TAG=<unique-tag> bash scripts/deploy.sh'),p('Use your own Service address for verification. The rollout script intentionally restarts the deployment.'),code('python scripts/verify.py http://<your-service-ip>\npython scripts/verify_rollout.py http://<your-service-ip>\nkubectl get pods -n poc-app -o wide\nkubectl top pods -n poc-app\nterraform -chdir=infrastructure plan -detailed-exitcode'),p('Troubleshoot image pulls with ACR digest and AcrPull permissions; blob 502 errors with logs, federation and RBAC; Pending pods with scheduling events and capacity. For a bad app revision use kubectl rollout undo deployment/app -n poc-app. Review cleanup commands in docs/SETUP.md: deleting the namespace and applying a reviewed Terraform destruction plan removes the app stack. Retain the separate backend until destruction and any required evidence export finish.'))
steady=json.loads((E/'steady-check.json').read_text()); initial=json.loads((E/'initial-check.json').read_text())
page('7. Public verification evidence',p('Recorded endpoint: http://4.236.11.192; availability today is unverified. Each public run checks the page, the two-item API, three upload/download/delete blob cycles, then 100 health requests using ten workers. Latencies include the client-to-westus3 network path.'),image('steady.png','Figure 4. Rendered saved output: steady-check.json; recorded at 15:09:39 UTC (16:09:39 Europe/Madrid).',600),table([('Sample','Failures','Median / p95 / max','Rate'),('Initial public','0 / 100','306.3 / 3825.9 / 4268.6 ms','15.2 req/s'),('Final public','0 / 100','306.7 / 448.1 / 541.4 ms','29.1 req/s'),('In-pod localhost','Not reported in summary','9.48 / 33.19 / not reported ms','709.3 req/s')]),p('Six blob cycles passed across the two public runs. The initial high tail latency is retained and has no proven root cause. The localhost sample used 200 requests and concurrency ten; it excludes public networking and storage. No per-request traces, confidence intervals or capacity conclusions are available.'))
page('8. Rolling updates and placement',p('The first restart passed 38 health checks but left both new replicas on one node. The original spread rule counted revisions together. Adding pod-template-hash to matchLabelKeys spreads each revision independently; probe timeouts were also increased to three seconds. The corrected restart passed 28 checks and ended with replicas on separate nodes.'),image('rollout.png','Figure 5. Rendered saved rollout.json; long JSON lines wrap for readability.',600),image('workloads.png','Figure 6. Rendered saved workloads.txt. Both pods are Ready, have zero restarts and occupy different nodes.',640),p('A successful rollout status alone does not prove final replica distribution. The placement snapshot supplies that separate check. These observations cover a rolling replacement; they do not demonstrate node-crash recovery or zone-outage survival.'))
page('9. Infrastructure and resource evidence',image('resources.png','Figure 7. Rendered saved resource snapshot: 47–59 millicores and 99–102 MiB per pod.',620),image('plan.png','Figure 8. Rendered terraform-plan.txt; subscription IDs were already redacted in the saved evidence.',640),p('The saved nodes.txt records two Ready nodes. RESULT.md reports ten resources created, no deletions and seven local tests passed; the saved plan directly records the no-change result. Resource usage is a point-in-time sample rather than a sustained peak.'))
page('10. Boundaries and source index',p('The endpoint is HTTP and the sample blob-write API has no authentication. Production follow-up would require TLS, API access control, centralized monitoring and alerts, budgets, recovery testing and deliberate availability/SLA choices. AKS Free, ACR Basic and LRS storage keep the PoC small but do not provide a zone-redundant design.'),p('The recorded four-vCPU regional/DSv4 quota is consumed by two nodes. A third node or node upgrade surge needs additional quota: at least six vCPUs, or eight to surge while three nodes run. Autoscaler max_count=3 is configuration, not proof of available quota or capacity.'),p('Primary implementation references, relative to the repository root:'),table([('Area','Source'),('Infrastructure','infrastructure/main.tf, variables.tf, outputs.tf, backend.tf, versions.tf'),('Workload','k8s/namespace.yaml; k8s/app.yaml'),('Application/image','src/backend/app.py; src/backend/dockerfile; src/backend/static/index.html'),('Delivery','scripts/bootstrap-backend.sh; deploy.sh; render.py'),('Verification','scripts/verify.py; verify_rollout.py; tests/'),('CI',' .github/workflows/deploy.yml'),('Recorded evidence','evidence/live-2026-11-01/*.json, *.txt and RESULT.md'),('Operational guides','README.md; docs/SETUP.md; docs/CI.md; docs/CASE-STUDY.md')]),p('Evidence provenance: Figures 4–8 reproduce saved files as images without making new cloud requests. The architecture diagrams were drawn from source configuration. This document excludes legacy root-level evidence for removed services. To regenerate: .venv/bin/python docs/build_documentation.py, then export the generated HTML to ODT using LibreOffice.'),p('Document prepared 1 November 2026. All measured results remain dated observations, not an uptime commitment or production throughput claim.'))
# Reader-oriented sections matching the supplied README structure.
page('Repository layout',code('.github/workflows/deploy.yml   Validation and optional app delivery\ninfrastructure/                AKS, ACR, Blob Storage and identity\nsrc/backend/                   Flask app, static page and Dockerfile\nk8s/                           Namespace and workload manifests\nscripts/                       Bootstrap, deploy, render and verify\ntests/                         Application and manifest tests\nevidence/live-2026-11-01/      Current-stack recorded results\ndocs/                          Setup, CI, case study and this document'),p('Start with infrastructure/main.tf for cloud resources, k8s/app.yaml for runtime controls, and src/backend/app.py for request behavior. The deployment script connects Terraform outputs to the Kubernetes renderer.'))
page('How the pieces connect',table([('Connection','Mechanism'),('Public requests','Client → public LoadBalancer → Service app → Ready Flask pod on port 8080'),('Image delivery','Docker → ACR → kubelet image pull using AcrPull → digest-pinned Deployment'),('App configuration','Terraform deployment output → deploy.sh environment → render.py → manifests'),('Blob authentication','Service-account token → AKS OIDC federation → app managed identity → DefaultAzureCredential'),('Blob authorization','Storage Blob Data Contributor scoped to the app-data container'),('Readiness and routing','Health probes determine Ready endpoints; storage is tested separately'),('CI login','GitHub OIDC → deployment identity; distinct from the app identity'),('State access','Bootstrap backend retains Terraform state; deployment reads outputs from that state')]),p('Unlike the supplied reference architecture, this implementation has one application container and a direct public Service. It does not implement Front Door, Application Gateway, ingress-nginx, PostgreSQL or Key Vault.'))
page('Known PoC shortcuts and hardening',table([('Current shortcut','Production follow-up'),('Public HTTP endpoint','Add managed TLS termination and HTTPS'),('Unauthenticated blob-write test','Protect the API with authentication, authorization and abuse controls'),('Single region; no explicit zone redundancy','Choose zonal node/storage options and test failure scenarios'),('AKS Free / ACR Basic / LRS','Select service tiers for the required availability and recovery objectives'),('Four-vCPU quota consumed by two nodes','Request node autoscaling and upgrade headroom before relying on it'),('Short checks and usage snapshots','Add sustained tests, centralized metrics/logs and alerting'),('Backend administration uses storage keys','Restrict state access and evaluate identity-based backend administration'),('Default cluster credential flow','Configure deliberate Entra/Kubernetes RBAC and API access restrictions')]),p('A disruption budget protects voluntary evictions. It does not establish node-failure recovery, zone resilience or an uptime SLA.'))
page('Cost and cleanup',p('The two AKS virtual machines, associated disks, LoadBalancer/public networking, ACR, Blob Storage and retained Terraform backend are the cost drivers. AKS Free refers to the control-plane tier; node infrastructure still incurs charges. No current price estimate is claimed in this document.'),p('Use the Azure cost view and calculator for your region, VM size, traffic and retention. Stop retaining unused deployments when the demonstration is complete. The state backend is separate and remains after destroying the application stack.'),p('Cleanup sequence from docs/SETUP.md; execute only against the intended subscription and cluster, after exporting required data:'),code('kubectl delete namespace poc-app --wait=true\nterraform -chdir=infrastructure plan -destroy -out=destroy.tfplan\n# Review the destruction plan before applying it.\nterraform -chdir=infrastructure apply destroy.tfplan'),p('Deleting the namespace first allows Kubernetes to release the managed LoadBalancer resources. Confirm removal in Azure. Remove the backend resource group only after destruction succeeds and only if it is dedicated to this project.'))
page('Troubleshooting',table([('Symptom','Check / action'),('Backend ResourceGroupNotFound','Run bootstrap-backend.sh; verify subscription and backend names'),('QuotaExceeded or node creation failure','Check regional and DSv4-family quotas, SKU availability and region capacity'),('ImagePullBackOff','Check image digest in ACR, kubelet AcrPull role and permission propagation'),('Storage API returns 503','AZURE_STORAGE_ACCOUNT_URL is unset; render and supply the storage endpoint'),('Storage API returns 502','Inspect app logs, client-ID annotation, pod label, federation subject and container role'),('Pending pod','Describe the pod; inspect capacity, events and topology-spread constraints'),('LoadBalancer address pending','Inspect Service events and allow Azure provisioning to complete'),('Metrics unavailable','Allow metrics collection for new pods; check metrics-server availability'),('ModuleNotFoundError: yaml','Activate .venv and install requirements-dev.txt')]),code('kubectl describe deployment app -n poc-app\nkubectl get events -n poc-app --sort-by=.lastTimestamp\nkubectl logs -n poc-app deployment/app\nkubectl get pods -n poc-app -o wide\nkubectl rollout history deployment/app -n poc-app'),p('For a bad application revision, kubectl rollout undo deployment/app -n poc-app rolls back the workload revision; it does not revert infrastructure changes.'))
# Reorder the existing evidence-rich document around the reference README outline.
order=[0,2,1,11,6,12,3,4,5,13,14,15,7,8,9,10]
pages=[pages[i] for i in order]
import re
for i in range(1,len(pages)):
    pages[i]=re.sub(r'<h1>(?:\d+\. )?([^<]+)</h1>',lambda m:f'<h1>{i}. {m.group(1)}</h1>',pages[i],count=1)
contents='Contents: '+ '; '.join(re.search(r'<h1>(.*?)</h1>',x).group(1) for x in pages[1:])+'.'
pages[0]=re.sub(r'<p>Contents:.*?</p>',p(contents),pages[0])

html='''<!DOCTYPE html><html><head><meta charset="utf-8"><title>Azure AKS PoC — Project Documentation</title><style>
@page { size:A4; margin:1.8cm; } body {font-family:Arial,sans-serif; font-size:10pt;color:#182b45;} h1 {font-size:22pt;color:#145c9b;} p {line-height:1.25;} section {page-break-before:always;} section:first-child {page-break-before:auto;} table {border-collapse:collapse;width:100%;font-size:9pt;} td {border:1px solid #cbd6e2;padding:6px;} tr:first-child {background:#e9f0f8;font-weight:bold;} pre {font-size:9pt;background:#eef2f6;white-space:pre-wrap;} .caption {font-size:8pt;color:#52657a;} img {max-width:100%;}
</style></head><body>'''+''.join(pages)+'</body></html>'
(ROOT/'docs/Azure-AKS-PoC-Documentation.html').write_text(html)
print('Generated HTML and nine evidence/diagram images.')

def embed_odt_images(path):
    """Make LibreOffice's HTML export portable by embedding linked PNG assets."""
    from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
    from xml.etree import ElementTree as ET
    with ZipFile(path) as z:
        entries={n:z.read(n) for n in z.namelist()}
    content=entries['content.xml'].decode()
    manifest=entries['META-INF/manifest.xml'].decode()
    ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}
    root=ET.fromstring(content)
    for im in root.findall('.//draw:image',ns):
        ref=im.attrib['{http://www.w3.org/1999/xlink}href']
        if ref.startswith('Pictures/'): continue
        name=Path(ref).name
        target='Pictures/'+name
        entries[target]=(OUT/name).read_bytes()
        content=content.replace(escape(ref,quote=True),target)
        manifest=manifest.replace('</manifest:manifest>',f'<manifest:file-entry manifest:full-path="{target}" manifest:media-type="image/png"/></manifest:manifest>')
    entries['content.xml']=content.encode()
    entries['META-INF/manifest.xml']=manifest.encode()
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('mimetype',entries.pop('mimetype'),compress_type=ZIP_STORED)
        for name,data in entries.items():z.writestr(name,data)

if __name__=='__main__':
    import sys
    if '--embed' in sys.argv:
        embed_odt_images(ROOT/'docs/Azure-AKS-PoC-Documentation.odt')
        print('Embedded images in portable ODT.')
