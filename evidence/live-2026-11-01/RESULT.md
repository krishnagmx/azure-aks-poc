# Live verification — November 1, 2026

App: http://4.236.11.192

- Terraform backend initialized; apply created 10 resources, with no deletions.
- Post-apply Terraform plan reported no changes.
- AKS: 2 Ready nodes; app: 2/2 Ready replicas on separate nodes, zero restarts.
- Final sampled usage: 47–59 millicores CPU and 99–102 MiB memory per app pod,
  within the configured 1 CPU / 256 MiB limits. This is a snapshot, not a peak.
- Page and items API passed. Six public blob upload/download/delete round trips
  passed across initial and final checks, using workload identity. No active test
  blobs remained afterward.
- Final public health sample: 100 requests, concurrency 10, no failures;
  median 306.7 ms, p95 448.1 ms, maximum 541.4 ms, 29.1 requests/second.
- The first sample shortly after deployment also had no failures but had a
  3825.9 ms p95; retained in initial-check.json rather than discarded.
- Localhost inside one pod: 200 requests at concurrency 10, median 9.48 ms,
  p95 33.19 ms, 709.3 requests/second. This excludes the public network and storage.
- First rolling restart: 38 health checks, no failures. It exposed both new
  replicas landing on one node. Added matchLabelKeys: [pod-template-hash] so each
  revision spreads independently, and increased health-probe timeouts to 3s.
- After that fix, a repeated restart passed 28 health checks without failures;
  both final replicas remained on separate nodes.
- Seven local application/rendering tests passed after the manifest changes.

These are short functional, small-load and rolling-update checks. They do not
establish production capacity, an availability SLA, zone failure tolerance, or
node-failure recovery. Public latency includes the client-to-westus3 network path.

Current quota is 4 regional/DSv4 vCPUs, fully consumed by the two nodes. A third
node or upgrade surge needs additional quota (at least 6 vCPUs, or 8 to surge
while running three nodes). The public endpoint uses HTTP and the demonstration
storage-write API is unauthenticated. The deployed Azure resources incur charges.
