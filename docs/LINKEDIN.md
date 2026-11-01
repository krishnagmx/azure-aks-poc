# LinkedIn publication kit

The copy below is a draft you can edit in your own voice. The PDF and PNGs are
ready to upload. No LinkedIn post has been published by this repository.

## Copy-ready post

I built and live-tested an Azure AKS PoC—and the most useful result was a bug the rollout test uncovered.

The project uses Terraform, one Python container, Azure Container Registry and Blob Storage. I simplified the original stack by removing an unused database, gateway, vault and Node proxy. The app uses workload identity instead of a storage connection-string secret.

What I verified:
• Two app replicas on separate nodes.
• Page/API checks and six blob upload/read/delete round trips.
• A final sample of 100 public health requests at concurrency 10: no failures, 307 ms median and 448 ms p95.
• A rolling restart with 28 successful health checks after the placement fix.

The first restart completed successfully but left both new pods on one node. I added revision-aware topology spreading, then repeated the test and checked the final node placement. That was a useful reminder: a green rollout does not prove every resilience assumption.

This is a small PoC, not a production-readiness or capacity claim. The repo includes the initial slower latency sample, raw verification results, setup/cleanup instructions and limitations.

I'm interested in discussing Azure, Cloud/DevOps and platform engineering opportunities. If you're hiring—or reviewing similar projects—I'd welcome your feedback.

Code and reproduction guide: https://github.com/krishnagmx/azure-aks-poc

#Azure #Kubernetes #Terraform #DevOps #CloudEngineering

## What to attach

Recommended: upload [aks-poc-linkedin.pdf](assets/aks-poc-linkedin.pdf) as a document
post. It has four portrait slides:

1. [Architecture](assets/01-architecture.png)
2. [Recorded verification](assets/02-verification.png)
3. [The rollout placement bug and fix](assets/03-rollout-lesson.png)
4. [Reproduction and limits](assets/04-reproduce.png)

Alternatively upload the four PNGs as photos in that order. The figures are
purpose-built explanations of recorded data, not screenshots of a dashboard.

Suggested document title: **Azure AKS PoC: architecture, testing and a rollout lesson**.

For a photo post, suggested alt text:

- Architecture: “One Python image in ACR deployed as two AKS replicas behind an Azure LoadBalancer, accessing private blob storage with workload identity.”
- Verification: “Recorded November 1, 2026: final 100-request public sample, concurrency 10, zero failures, median 306.7 ms and p95 448.1 ms; first-run p95 was 3825.9 ms.”
- Rollout: “Initial rollout placed both new replicas on one node. Adding pod-template-hash to topology spread matching preserved separate-node placement after a second restart, with 28 successful health checks.”
- Reproduce: “Clone the repository, test locally, bootstrap and apply Terraform, deploy, verify and clean up. PoC limits include HTTP, no zone redundancy and quota constraints.”

## Publish it yourself

1. Open your LinkedIn home feed and choose **Start a post**.
2. Paste the copy above and edit the job-interest sentence to match your actual
   target roles. Check the repository link and the claims against the evidence.
3. Choose **More → Add a document**, select the PDF and enter the suggested title.
   Review all four slides before publishing. If you prefer photos, use the photo
   option and upload the PNGs instead. A photo attachment replaces a URL-preview
   attachment; keep the repository URL as text, or add it in a comment if the
   composer does not retain it.
4. Choose your intended audience, review the post and publish it.
5. Open the post's **More** menu and add it to your profile's **Featured** section
   when that option is available. You can also add the GitHub repository as a
   separate Featured link from your profile.
6. Add the repository link and the short project description from CASE-STUDY.md
   to your profile's Projects section if that section is available on your account.

UI wording can vary. Official LinkedIn help: [documents](https://www.linkedin.com/help/linkedin/answer/a518909),
[photos](https://www.linkedin.com/help/linkedin/answer/a527229),
[Featured section](https://www.linkedin.com/help/linkedin/answer/a552452/featured-section-on-your-profile-faqs).

## Speak to a recruiter

Use the [45-second explanation](CASE-STUDY.md#talking-about-the-project), then
ask which part of the role's stack is most relevant. Lead with the problem,
your design decision, the test result and what you learned. The strongest example
is the placement bug: explain what you expected, what you observed, what you changed
and how you retested it.

Example connection/follow-up message (send personally, after checking relevance):

“Hi [Name], I saw your [Cloud/DevOps] opening. I recently built and live-tested an
Azure AKS project with Terraform, workload identity and rolling-update checks.
The repository includes reproduction steps and verification evidence:
https://github.com/krishnagmx/azure-aks-poc. I'd be interested to hear whether
that experience is relevant to your team.”

Do not imply a production deployment, certification, availability SLA, proven
node-failure recovery or sustained capacity. If asked about AI assistance, describe
the tools you used honestly and be prepared to explain every design and test.

## Regenerate the visuals

```sh
python -m pip install -r docs/requirements-visuals.txt
python docs/build_visuals.py
```

The script reads the committed JSON evidence and exports four PNGs and one PDF.
It does not collect a new measurement or take a screenshot.
