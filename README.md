# AI Arcade

Twelve short games built from MIT course activities, prototyped for MIT Learn. Each game opens with a goal, plays out as you move things, and explains the idea once you finish.

**Play:** https://codey-m.github.io/ai-arcade/

Games appear in play order, not course order: the subjects alternate, each statistics puzzle comes before the game that applies it (Beach Beeps before Photo Finish, Mean Flights before Wonder Fold), and each course's games otherwise keep their course order. Pairing Bench goes in after Downhill Racer when it joins.

| Game | Course | Idea |
| --- | --- | --- |
| [Beach Beeps](https://codey-m.github.io/ai-arcade/beach-beeps.html) | Probability+SDA 6.3710.1x | Bayes' rule and the base rate |
| [Recycling Day](https://codey-m.github.io/ai-arcade/sort-the-recycling.html) | Deep Learning 6.7960.1x | Model capacity: building and training a small network |
| [Backup Power](https://codey-m.github.io/ai-arcade/backup-power.html) | Probability+SDA 6.3710.1x | Independence and reliability |
| [Rover Route](https://codey-m.github.io/ai-arcade/trace-the-trail.html) | Deep Learning 6.7960.1x | Generalization: fitting measurements without following their noise |
| [Prize Wheel](https://codey-m.github.io/ai-arcade/prize-wheel.html) | Probability+SDA 6.3710.2x | Distributions with the same average and different chances |
| [Downhill Racer](https://codey-m.github.io/ai-arcade/guide-the-robot-home.html) | Deep Learning 6.7960.2x | Learning rate, momentum and local minima |
| [Lookout Tower](https://codey-m.github.io/ai-arcade/lookout-tower.html) | Deep Learning 6.7960.3x | Convolution, stride and the receptive field |
| [Photo Finish](https://codey-m.github.io/ai-arcade/photo-finish.html) | Deep Learning 6.7960.2x | Accuracy, precision and recall with a rare class |
| [Echo Dancer](https://codey-m.github.io/ai-arcade/echo-the-dance.html) | Deep Learning 6.7960.4x | Principal component analysis |
| [Wonder Fold](https://codey-m.github.io/ai-arcade/the-wonder-fold.html) | Probability+SDA 6.3710.5x | Sample size and the power of a test |
| [Next Note](https://codey-m.github.io/ai-arcade/next-note.html) | Deep Learning 6.7960.5x | Generating one piece at a time: temperature and top-k sampling |
| [Robot Theatre](https://codey-m.github.io/ai-arcade/robot-theatre.html) | CV+NLP 6.4600.1x | Bag-of-words features, word order and bigrams |

## Demo tips

- Every game is one self-contained HTML file. It runs offline, stores nothing and makes no network requests, so a downloaded copy works too.
- Add `?embed=1` to a game's link to see it as it would sit inside a course lesson, without the arcade title bar.
- Add `?seed=` with a number to open a specific round, for example `photo-finish.html?seed=7`. Without it, each game opens on its introductory round. The address bar always holds the round you are on, so copying it shares that round.

## How this repository works

The games are developed and tested in the `ai-arcade-review/pilots` working folder, not here. This repository holds the playable site and the scripts that assemble it.

- `site/` is the published site: the launcher (`index.html`), one HTML file per game and the card thumbnails.
- `games.json` lists the games in launcher order: title, card text, course, colour, and which built file in the pilots folder each one comes from.
- `launcher.html` is the launcher template.
- `sync.py` copies the built games into `site/`, removes review-only links (build notes and archived course originals) and writes `site/index.html`. It stops if any other link would leave the site.
- `tools/thumbs.py` redraws the thumbnails (macOS with Google Chrome). It hides all text first, because course images carry no words; each card's alt text describes the scene.
- `.github/workflows/pages.yml` publishes `site/` to GitHub Pages on every push to `main` that changes `site/`. You can also run it by hand from the Actions tab.

## Updating the site

```sh
# 1. Build the games in the pilots folder (each game's own build.py, or the shared one).
cd ../ai-arcade-review/pilots && python3 build.py && python3 echo-dance/build.py && python3 wonder-fold/build.py

# 2. Copy them here and refresh the launcher. Redraw thumbnails when a game looks different.
cd ../../ai-arcade && python3 sync.py && python3 tools/thumbs.py && python3 sync.py

# 3. Review, then commit and push. The site updates a minute or two after the push.
git add -A && git commit -m "Update games" && git push
```

A game marked `"hold": true` in `games.json` keeps its place in the order but stays off the site (Mean Flights, while it is reworked as Tipping Point). To add a game, add an entry to `games.json` with its built file name and the CSS selector of its play area (used for the thumbnail), then run step 2. Two optional fields shape the thumbnail: `thumb_steps` plays the game into a more telling state first (selectors to click, or `{"set": selector, "value": v}` for a slider), `thumb_zoom` crops a wide play area at its centre instead of padding it (`"fill"` trims a tall one too, so the scene fills the card), and `thumb_query` opens a particular round (for example `seed=4`).
