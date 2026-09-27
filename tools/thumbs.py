#!/usr/bin/env python3
"""Refresh the launcher thumbnails in site/thumbs/ (macOS: Google Chrome + sips).

Each game opens headless at 1280 px with reduced motion. The play area named by
"play" in games.json is cropped to 16:10 around its centre. All text is hidden
first, because course images carry no words or numbers; each card's alt text
describes the scene instead. Run sync.py first, then this, then sync.py again.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
SITE = HERE / 'site'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
WIDTH, HEIGHT, SCALE, OUT_WIDTH, ASPECT = 1280, 1400, 2, 960, 1.6

HIDE_TEXT = '''<style>
*{color:transparent!important;text-shadow:none!important;caret-color:transparent!important}
text,tspan{fill:transparent!important;stroke:transparent!important}
.corner,.stack-count,.route-tag,.gate-grip>span,.frame-label{visibility:hidden!important}
</style>'''
PROBE = '''<script>addEventListener('load',()=>setTimeout(()=>{const e=document.querySelector(%s);const r=e.getBoundingClientRect();
document.body.setAttribute('data-thumb',[r.left+scrollX,r.top+scrollY,r.width,r.height].map(Math.round).join(','));},1500));</script>'''


def chrome(*args):
    base = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-prefers-reduced-motion',
            f'--window-size={WIDTH},{HEIGHT}', f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=5000']
    return subprocess.run(base + list(args), capture_output=True, text=True, timeout=120)


def box(x, y, w, h):
    """Grow the play area to 16:10 around its centre, kept inside the captured window."""
    if w / h > ASPECT:
        h2, w2 = w / ASPECT, w
    else:
        h2, w2 = h, h * ASPECT
    cx, cy = x + w / 2, y + h / 2
    x0 = min(max(cx - w2 / 2, 0), WIDTH - w2)
    y0 = min(max(cy - h2 / 2, 0), HEIGHT - h2)
    return [round(v * SCALE) for v in (x0, y0, w2, h2)]


def main(only=()):
    games = json.loads((HERE / 'games.json').read_text())['games']
    (SITE / 'thumbs').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for game in games:
            if only and game['slug'] not in only:
                continue
            page = (SITE / f'{game["slug"]}.html').read_text()
            page = page.replace('</head>', HIDE_TEXT + '</head>', 1).replace('</body>', PROBE % json.dumps(game['play']) + '</body>', 1)
            probe = Path(tmp) / f'{game["slug"]}.html'
            probe.write_text(page)
            dom = chrome('--dump-dom', probe.as_uri()).stdout
            m = re.search(r'data-thumb="([\d,.-]+)"', dom)
            if not m:
                print(f'{game["slug"]}: play area {game["play"]} not found; skipped', file=sys.stderr)
                continue
            x, y, w, h = box(*map(float, m.group(1).split(',')))
            shot = Path(tmp) / f'{game["slug"]}.png'
            chrome(f'--screenshot={shot}', probe.as_uri())
            out = SITE / 'thumbs' / f'{game["slug"]}.jpg'
            subprocess.run(['sips', '-c', str(h), str(w), '--cropOffset', str(y), str(x), str(shot), '--out', str(shot)], check=True, capture_output=True)
            subprocess.run(['sips', '--resampleWidth', str(OUT_WIDTH), '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(shot), '--out', str(out)], check=True, capture_output=True)
            print(f'thumbs/{out.name}  ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main(set(sys.argv[1:]))
