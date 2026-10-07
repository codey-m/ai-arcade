#!/usr/bin/env python3
"""Refresh the launcher thumbnails in site/thumbs/ (macOS: Google Chrome + sips).

Each game opens headless at 1280 px with reduced motion. The play area named by
"play" in games.json is cropped to 16:10 around its centre. All text is hidden
first, because course images carry no words or numbers; each card's alt text
describes the scene instead. Optional "thumb_steps" in games.json plays the game
into a more telling state first (buttons to press, sliders to set), and
"thumb_query" opens a particular round (for example "seed=4").
Run sync.py first, then this, then sync.py again.
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

def hide(play):
    """Hide all text, and everything outside the play area, so the picture is the scene alone."""
    return f'''<style>
*{{color:transparent!important;text-shadow:none!important;caret-color:transparent!important}}
text,tspan{{fill:transparent!important;stroke:transparent!important}}
body *{{visibility:hidden!important}}{play},{play} *{{visibility:visible!important}}
{play} .corner,{play} .stack-count,{play} .route-tag,{play} .gate-grip>span,{play} .frame-label{{visibility:hidden!important}}
</style>'''


# Runs the optional "thumb_steps" (a selector to click, SVG elements included, or {"set": selector, "value": v} for a slider),
# 400 ms apart, then measures the play area once the result has settled.
PROBE = '''<script>addEventListener('load',()=>{const steps=%s;let i=0;const next=()=>{if(i<steps.length){const t=steps[i++];
if(typeof t==='string'){const e=document.querySelector(t);if(e&&e.click)e.click();else if(e)e.dispatchEvent(new MouseEvent('click',{bubbles:true}));}else{const e=document.querySelector(t.set);if(e){e.value=t.value;
e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}}setTimeout(next,400);return;}
setTimeout(()=>{const e=document.querySelector(%s);const r=e.getBoundingClientRect();
document.body.setAttribute('data-thumb',[r.left+scrollX,r.top+scrollY,r.width,r.height].map(Math.round).join(','));},2500);};setTimeout(next,800);});</script>'''


def chrome(*args):
    base = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-prefers-reduced-motion',
            f'--window-size={WIDTH},{HEIGHT}', f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=12000']
    return subprocess.run(base + list(args), capture_output=True, text=True, timeout=120)


def box(x, y, w, h, zoom=False):
    """Grow the play area to 16:10 around its centre, kept inside the captured window.
    With zoom, a wide play area is trimmed to 16:10 at its centre instead of padded; with zoom "fill",
    a tall one is trimmed too, so the scene fills the card."""
    if zoom and w / h > ASPECT:
        h2, w2 = h, h * ASPECT
    elif zoom == 'fill':
        w2, h2 = w, w / ASPECT
    elif w / h > ASPECT:
        h2, w2 = w / ASPECT, w
    else:
        h2, w2 = h, h * ASPECT
    cx, cy = x + w / 2, y + h / 2
    x0 = min(max(cx - w2 / 2, 0), WIDTH - w2)
    y0 = min(max(cy - h2 / 2, 0), HEIGHT - h2)
    return [round(v * SCALE) for v in (x0, y0, w2, h2)]


def main(only=()):
    games = [g for g in json.loads((HERE / 'games.json').read_text())['games'] if not g.get('hold')]
    (SITE / 'thumbs').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for game in games:
            if only and game['slug'] not in only:
                continue
            page = (SITE / f'{game["slug"]}.html').read_text()
            page = page.replace('</head>', hide(game['play']) + '</head>', 1).replace('</body>', PROBE % (json.dumps(game.get('thumb_steps', [])), json.dumps(game['play'])) + '</body>', 1)
            probe = Path(tmp) / f'{game["slug"]}.html'
            probe.write_text(page)
            url = probe.as_uri() + ('?' + game['thumb_query'] if game.get('thumb_query') else '')
            dom = chrome('--dump-dom', url).stdout
            m = re.search(r'data-thumb="([\d,.-]+)"', dom)
            if not m:
                print(f'{game["slug"]}: play area {game["play"]} not found; skipped', file=sys.stderr)
                continue
            x, y, w, h = box(*map(float, m.group(1).split(',')), zoom=game.get('thumb_zoom', False))
            shot = Path(tmp) / f'{game["slug"]}.png'
            chrome(f'--screenshot={shot}', url)
            out = SITE / 'thumbs' / f'{game["slug"]}.jpg'
            subprocess.run(['sips', '-c', str(h), str(w), '--cropOffset', str(y), str(x), str(shot), '--out', str(shot)], check=True, capture_output=True)
            subprocess.run(['sips', '--resampleWidth', str(OUT_WIDTH), '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(shot), '--out', str(out)], check=True, capture_output=True)
            print(f'thumbs/{out.name}  ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main(set(sys.argv[1:]))
