#!/usr/bin/env python3
"""Copy the built games from the pilots working folder into site/ and write the launcher.

The games are built where they are developed (ai-arcade-review/pilots). This script
only copies them. It removes review-only links (build notes, archived course
originals, the full widget review), which are not part of the public site, and fails
if any other link would leave site/.

    python3 sync.py            # copy games, write site/index.html
    python3 tools/thumbs.py    # optional: refresh site/thumbs/ (macOS, Google Chrome)
"""
from pathlib import Path
import html
import json
import re

HERE = Path(__file__).resolve().parent
SITE = HERE / 'site'
CONFIG = json.loads((HERE / 'games.json').read_text())
PILOTS = (HERE / CONFIG['pilots']).resolve()

# In the shared shell, app.js writes into #about and #original, so those two stay as hidden stubs.
ABOUT = re.compile(r'<details class="review-about">.*?</details>', re.S)
STUB = '<div hidden><p id="about"></p><span id="original"></span></div>'
REVIEW_NAV = '<a href="../index.html">Widget review ↗</a>'
# The shared shell still carries the old review header; JS hides it, but it would show before the script runs.
REVIEW_HEADER = re.compile(r'<header><nav class="topnav".*?</nav></header>', re.S)
NOSCRIPT_OLD = 'These interactive pilots need JavaScript enabled. The full design review remains readable without it.'
ALLOWED = re.compile(r'^(index\.html|#.*|data:.*|\$\{.*\})$')
# Arcade icon (gamepad in MIT red), inlined so no page requests /favicon.ico.
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect x='2' y='8' width='28' height='17' rx='8.5' fill='%23750014'/%3E"
        "%3Cpath d='M9 13v7M5.5 16.5h7' stroke='white' stroke-width='2.4' stroke-linecap='round'/%3E"
        "%3Ccircle cx='21' cy='14.5' r='1.8' fill='white'/%3E%3Ccircle cx='24.5' cy='18.5' r='1.8' fill='white'/%3E%3C/svg%3E")


def clean(text, game):
    blocks = ABOUT.findall(text)
    assert len(blocks) == 1, f'{game["source"]}: expected one review-about block, found {len(blocks)}'
    text = ABOUT.sub(STUB if 'id="about"' in blocks[0] else '', text)
    text = REVIEW_HEADER.sub('', text, count=1)
    text = text.replace(REVIEW_NAV, '').replace(NOSCRIPT_OLD, 'This game needs JavaScript.')
    text, n = re.subn(r'<title>[^<]*</title>', f'<title>{html.escape(game["title"])} · AI Arcade</title><link rel="icon" href="{ICON}">', text, count=1)
    assert n == 1, f'{game["source"]}: no <title>'
    for attr in re.findall(r'\b(?:href|src)="([^"]*)"', text):
        assert ALLOWED.match(attr), f'{game["source"]}: link would leave the site: {attr}'
    return text


def card(i, game):
    thumb = SITE / 'thumbs' / f'{game["slug"]}.jpg'
    shot = (f'<img src="thumbs/{game["slug"]}.jpg" alt="{html.escape(game["alt"])}" loading="lazy" width="960" height="600">'
            if thumb.exists() else '<span class="noshot" aria-hidden="true"></span>')
    return f'''      <li><a class="game" href="{game["slug"]}.html" style="--course:{game["colour"]}" aria-labelledby="t-{game["slug"]}" aria-describedby="h-{game["slug"]}">
        <span class="shot">{shot}<span class="num" aria-hidden="true">{i:02d}</span></span>
        <span class="body">
          <span class="course"><i aria-hidden="true"></i>{html.escape(game["course"])} · {html.escape(game["topic"])}</span>
          <h2 id="t-{game["slug"]}">{html.escape(game["title"])}</h2>
          <span class="hook" id="h-{game["slug"]}">{html.escape(game["hook"])}</span>
          <span class="foot"><span class="play">Play<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="code">{html.escape(game["number"])}</span></span>
        </span>
      </a></li>'''


def main():
    games = CONFIG['games']
    assert len({g['slug'] for g in games}) == len(games), 'duplicate slug'
    SITE.mkdir(exist_ok=True)
    for game in games:
        source = PILOTS / game['source']
        (SITE / f'{game["slug"]}.html').write_text(clean(source.read_text(), game))
        print(f'{game["slug"]}.html  <-  {source.relative_to(PILOTS.parent)}')
    known = {f'{g["slug"]}.html' for g in games} | {'index.html'}
    for stale in SITE.glob('*.html'):
        if stale.name not in known:
            stale.unlink()
            print('removed', stale.name)
    page = (HERE / 'launcher.html').read_text()
    page = page.replace('__CARDS__', '\n'.join(card(i, g) for i, g in enumerate(games, 1)))
    page = page.replace('__COUNT__', str(len(games))).replace('__REPO__', CONFIG['repo']).replace('__ICON__', ICON)
    (SITE / 'index.html').write_text(page)
    (SITE / '.nojekyll').write_text('')
    missing = [g['slug'] for g in games if not (SITE / 'thumbs' / f'{g["slug"]}.jpg').exists()]
    print(f'index.html with {len(games)} games' + (f'; no thumbnail yet for {", ".join(missing)} (run tools/thumbs.py)' if missing else ''))


if __name__ == '__main__':
    main()
