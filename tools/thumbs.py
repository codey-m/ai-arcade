#!/usr/bin/env python3
"""Refresh the launcher thumbnails in site/thumbs/ (macOS: Google Chrome + sips).

Each game opens headless at 1280 px with reduced motion. The play area named by
"play" in games.json is cropped whole with a margin, then padded to 16:10 on white,
centred, so every card shows its complete scene in the same framed, wide format. All text is hidden
first, because course images carry no words or numbers; each card's alt text
describes the scene instead. Optional "thumb_steps" in games.json plays the game
into a more telling state first (buttons to press, sliders to set, keys to press),
and "thumb_query" opens a particular round (for example "seed=4"). With
"thumb_live": {"steps": [...], "after": ms}, the game is then played on in real time
and caught mid-animation (tools/live.py), for planes in flight or crates in the air.
Run sync.py first, then this, then sync.py again.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
SITE = HERE / 'site'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
WIDTH, HEIGHT, SCALE, OUT_WIDTH, ASPECT, MARGIN = 1280, 1400, 2, 960, 1.6, 24

def hide(play):
    """Hide all text, and everything outside the play area, so the picture is the scene alone."""
    return f'''<style>
*{{color:transparent!important;text-shadow:none!important;caret-color:transparent!important}}
text,tspan{{fill:transparent!important;stroke:transparent!important}}
body *{{visibility:hidden!important}}{play},{play} *{{visibility:visible!important}}
{play} .corner,{play} .stack-count,{play} .route-tag,{play} .gate-grip>span,{play} .frame-label,{play} .place-no,{play} .set-total{{visibility:hidden!important}}
</style>'''


# Runs the optional "thumb_steps" (a selector to click, SVG elements included, {"set": selector, "value": v} for a slider,
# or {"key": selector, "press": key, "times": n} for keyboard controls),
# 400 ms apart, then measures the play area once the result has settled.
PROBE = '''<script>addEventListener('load',()=>{const steps=%s;let i=0;const next=()=>{if(i<steps.length){const t=steps[i++];
if(typeof t==='string'){const e=document.querySelector(t);if(e&&e.click)e.click();else if(e)e.dispatchEvent(new MouseEvent('click',{bubbles:true}));}else if(t.key){const e=document.querySelector(t.key);for(let i=0;i<(t.times||1);i++)e&&e.dispatchEvent(new KeyboardEvent('keydown',{key:t.press,bubbles:true,cancelable:true}));}else{const e=document.querySelector(t.set);if(e){e.value=t.value;
e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}}setTimeout(next,400);return;}
setTimeout(()=>{const e=document.querySelector(%s);const r=e.getBoundingClientRect();
document.body.setAttribute('data-thumb',[r.left+scrollX,r.top+scrollY,r.width,r.height].map(Math.round).join(','));},2500);};setTimeout(next,800);});</script>'''


def chrome(*args):
    base = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-prefers-reduced-motion',
            f'--window-size={WIDTH},{HEIGHT}', f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=12000']
    return subprocess.run(base + list(args), capture_output=True, text=True, timeout=120)


def box(x, y, w, h, margin=MARGIN):
    """The whole play area plus a margin, in screenshot pixels. Every scene is shown complete, never trimmed;
    padding to 16:10 happens afterwards, centred, so a scene's position on the page doesn't matter."""
    x0, y0 = max(x - margin, 0), max(y - margin, 0)
    x1, y1 = min(x + w + margin, WIDTH), min(y + h + margin, HEIGHT)
    return [round(v * SCALE) for v in (x0, y0, x1 - x0, y1 - y0)]


def padded(w, h):
    """The 16:10 frame that holds a w x h crop with the crop centred: bands above and below a wide scene,
    at the sides of a tall one."""
    return (round(max(h, w / ASPECT)), round(max(w, h * ASPECT)))


def main(only=()):
    games = [g for g in json.loads((HERE / 'games.json').read_text())['games'] if not g.get('hold')]
    (SITE / 'thumbs').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for game in games:
            if only and game['slug'] not in only:
                continue
            page = (SITE / f'{game["slug"]}.html').read_text().replace('</head>', hide(game['play']) + '</head>', 1)
            probe = Path(tmp) / f'{game["slug"]}.html'
            url = probe.as_uri() + ('?' + game['thumb_query'] if game.get('thumb_query') else '')
            shot = Path(tmp) / f'{game["slug"]}.png'
            out = SITE / 'thumbs' / f'{game["slug"]}.jpg'
            if game.get('thumb_live'):
                probe.write_text(page)
                live.capture(CHROME, url, game['play'], game.get('thumb_steps', []), game['thumb_live'], str(shot), box, (WIDTH, HEIGHT, SCALE))
                w, h = map(int, subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(shot)], capture_output=True, text=True).stdout.split()[-3::2])
                finish(shot, w, h, out)
                continue
            probe.write_text(page.replace('</body>', PROBE % (json.dumps(game.get('thumb_steps', [])), json.dumps(game['play'])) + '</body>', 1))
            dom = chrome('--dump-dom', url).stdout
            m = re.search(r'data-thumb="([\d,.-]+)"', dom)
            if not m:
                print(f'{game["slug"]}: play area {game["play"]} not found; skipped', file=sys.stderr)
                continue
            x, y, w, h = box(*map(float, m.group(1).split(',')))
            chrome(f'--screenshot={shot}', url)
            subprocess.run(['sips', '-c', str(h), str(w), '--cropOffset', str(y), str(x), str(shot), '--out', str(shot)], check=True, capture_output=True)
            finish(shot, w, h, out)


def finish(shot, w, h, out):
    """Pad the cropped scene to 16:10 on white, centred, and save it as the card's JPEG."""
    ph, pw = padded(w, h)
    subprocess.run(['sips', '--padToHeightWidth', str(ph), str(pw), '--padColor', 'FFFFFF', str(shot), '--out', str(shot)], check=True, capture_output=True)
    subprocess.run(['sips', '--resampleWidth', str(OUT_WIDTH), '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(shot), '--out', str(out)], check=True, capture_output=True)
    print(f'thumbs/{out.name}  ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main(set(sys.argv[1:]))
