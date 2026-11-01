"""Export explanatory PNGs/PDF from recorded evidence; not dashboard screenshots.

Run: python -m pip install -r docs/requirements-visuals.txt
     python docs/build_visuals.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/assets'
EVIDENCE = ROOT / 'evidence/live-2026-11-01'
steady = json.loads((EVIDENCE / 'steady-check.json').read_text())
initial = json.loads((EVIDENCE / 'initial-check.json').read_text())
rollout = json.loads((EVIDENCE / 'rollout.json').read_text())
BG, INK, MUTED, BLUE, TEAL, WHITE = '#f4f6fa', '#12233f', '#506079', '#1763df', '#087f75', '#ffffff'


def font(size, bold=False):
    candidates = [
        f'/System/Library/Fonts/Supplemental/Arial{" Bold" if bold else ""}.ttf',
        f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf',
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def text(x, y, value, size=32, color=INK, bold=False):
    d.multiline_text((x, y), value, font=font(size, bold), fill=color, spacing=14)


def card(box, fill=WHITE, outline=None):
    d.rounded_rectangle(box, radius=24, fill=fill, outline=outline, width=2)


def arrow(start, end):
    d.line((start, end), fill=BLUE, width=5)
    x, y = end
    d.polygon([(x, y), (x-10, y-16), (x+10, y-16)], fill=BLUE)


def page(number, title, subtitle):
    global d
    im = Image.new('RGB', (1080, 1350), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1080, 14), fill=BLUE)
    text(64, 54, 'AZURE  /  KUBERNETES  /  TERRAFORM', 23, BLUE, True)
    text(64, 108, title, 64, bold=True)
    text(64, 275, subtitle, 28, MUTED)
    d.line((64, 1242, 1016, 1242), fill='#d2dae7', width=2)
    text(64, 1264, 'github.com/krishnagmx/azure-aks-poc', 24, MUTED)
    text(940, 1264, f'{number}/4', 24, BLUE, True)
    return im


images = []
im = page(1, 'One app.\nTwo AKS replicas.', 'A smaller stack, with app identity instead of a storage secret.')
card((64, 350, 1016, 430)); text(100, 372, 'Browser  →  Azure LoadBalancer (HTTP)', 34, bold=True)
arrow((540, 435), (540, 500))
card((64, 505, 1016, 820), '#e5edfc')
text(100, 530, 'AKS  /  TWO-NODE POOL', 26, BLUE, True)
for x, label in [(96, 'Node A'), (558, 'Node B')]:
    card((x, 590, x+426, 775))
    text(x+28, 613, label, 30, MUTED)
    text(x+28, 666, 'Python app replica', 31, bold=True)
    text(x+28, 717, 'Same immutable image', 24, MUTED)
arrow((540, 825), (540, 908))
text(577, 852, 'Workload identity', 26, TEAL, True)
card((64, 918, 1016, 1022)); text(100, 948, 'Private blob container: app-data', 34, bold=True)
card((64, 1060, 1016, 1178), INK)
text(94, 1082, 'ACR stores one image; deployment pins its digest.', 29, WHITE)
text(94, 1128, 'Terraform provisions 10 resources in one root configuration.', 25, '#c7d6ed')
images.append(('01-architecture', im))

im = page(2, 'Evidence,\nwith its limits.', 'Recorded live check  /  November 1, 2026  /  westus3')
metrics = [
    ('Health requests', str(steady['health_requests']), '10 concurrent clients'),
    ('Request failures', str(steady['failures']), 'In the final public sample'),
    ('Median latency', f"{steady['health_latency_ms']['median']:.1f} ms", 'Public client-to-app path'),
    ('p95 latency', f"{steady['health_latency_ms']['p95']:.1f} ms", 'Public client-to-app path'),
]
for i, (label, value, note) in enumerate(metrics):
    x, y = 64 + (i%2)*488, 355 + (i//2)*238
    card((x, y, x+464, y+214))
    text(x+28, y+25, label, 27, MUTED)
    text(x+28, y+77, value, 55, TEAL, True)
    text(x+28, y+159, note, 23, MUTED)
card((64, 855, 1016, 1000), INK)
cycles = initial['storage_round_trips'] + steady['storage_round_trips']
text(94, 880, f'{cycles} blob upload / read / delete cycles passed', 32, WHITE, True)
text(94, 934, 'Two Ready replicas on separate nodes; zero restarts.', 28, '#c7d6ed')
text(64, 1040, f"First-run p95: {initial['health_latency_ms']['p95']:.1f} ms (also retained).", 30, bold=True)
text(64, 1100, 'Short samples. No production capacity or uptime claim.\nSource: evidence/live-2026-11-01/*.json', 27, MUTED)
images.append(('02-verification', im))

im = page(3, 'A green rollout hid\na placement bug.', 'Testing the final state mattered as much as rollout success.')
text(64, 355, 'OBSERVED AFTER THE FIRST RESTART', 25, MUTED, True)
for x, label, value in [(64, 'Node A', '0 new replicas'), (552, 'Node B', '2 new replicas')]:
    card((x, 410, x+464, 565)); text(x+30, 435, label, 28, MUTED);text(x+30, 490, value, 33, bold=True)
card((64, 612, 1016, 795), INK)
text(94, 638, 'Fix: spread each revision independently', 31, WHITE, True)
text(94, 701, 'matchLabelKeys: [pod-template-hash]', 33, '#8fc4ff')
text(64, 842, 'VERIFIED AFTER ANOTHER RESTART', 25, TEAL, True)
for x, label in [(64, 'Node A'), (552, 'Node B')]:
    card((x, 896, x+464, 1037)); text(x+30, 918, label, 28, MUTED);text(x+30, 971, '1 Ready replica', 33, TEAL, True)
text(64, 1085, f"{rollout['health_checks_during_rollout']} health checks; {len(rollout['failures'])} observed request failures.", 32, bold=True)
text(64, 1141, 'Recorded outputs: rollout.json and workloads.txt\nIllustration of recorded state; not a dashboard screenshot.', 24, MUTED)
images.append(('03-rollout-lesson', im))

im = page(4, 'Clone it. Run it.\nCheck the evidence.', 'Setup, troubleshooting and cleanup are included in GitHub.')
steps = [
    ('01', 'Run locally', 'Clone → virtual environment → seven local tests.'),
    ('02', 'Provision Azure', 'Choose your subscription → backend → Terraform plan/apply.'),
    ('03', 'Deploy and verify', 'Build one image → digest-pinned rollout → HTTP/blob checks.'),
    ('04', 'Inspect and clean up', 'Review raw results → remove app resources when finished.'),
]
for i, (number, title, detail) in enumerate(steps):
    y=360+i*164
    card((64,y,1016,y+140));text(91,y+23,number,39,BLUE,True)
    text(175,y+22,title,34,bold=True);text(175,y+79,detail,25,MUTED)
card((64, 1052, 1016, 1195), INK)
text(94, 1075, 'Deliberately a PoC, not production-ready.', 32, WHITE, True)
text(94, 1127, 'HTTP • no zone redundancy • quota headroom needed\nAzure resources incur charges. No proven node-failure recovery.', 25, '#c7d6ed')
images.append(('04-reproduce', im))

OUT.mkdir(parents=True, exist_ok=True)
for name, im in images:
    im.save(OUT/f'{name}.png', optimize=True)
images[0][1].save(OUT/'aks-poc-linkedin.pdf', save_all=True,
                  append_images=[im for _, im in images[1:]], resolution=144)
print('Exported four PNG slides and a four-page PDF from recorded evidence.')
