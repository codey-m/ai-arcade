# AI Arcade

Eighteen short games built from MIT course activities, prototyped for MIT Learn. Each game opens with a goal and keeps its explanation in a closed drop-down.

**Play:** https://codey-m.github.io/ai-arcade/

Games appear in play order, not course order: the subjects alternate, each statistics puzzle comes before the game that applies it (Beach Beeps before Photo Finish, Tipping Point before Wonder Fold), and each course's games otherwise keep their course order.

| Game | Course | Idea |
| --- | --- | --- |
| [Beach Beeps](https://codey-m.github.io/ai-arcade/beach-beeps.html) | Probability+SDA 6.3710.1x | Bayes' rule and the base rate |
| [Recycling Day](https://codey-m.github.io/ai-arcade/sort-the-recycling.html) | Deep Learning 6.7960.1x | Model capacity: building and training a small network |
| [Backup Power](https://codey-m.github.io/ai-arcade/backup-power.html) | Probability+SDA 6.3710.1x | Independence and reliability |
| [Transfer Desk](https://codey-m.github.io/ai-arcade/transfer-desk.html) | AI Systems+Agents 6.S978.1x | Enforcing requirements: diagnosing and repairing a payment desk |
| [Rover Route](https://codey-m.github.io/ai-arcade/trace-the-trail.html) | Deep Learning 6.7960.1x | Generalization: fitting measurements without following their noise |
| [Prize Wheel](https://codey-m.github.io/ai-arcade/prize-wheel.html) | Probability+SDA 6.3710.2x | Distributions with the same average and different chances |
| [Downhill Racer](https://codey-m.github.io/ai-arcade/guide-the-robot-home.html) | Deep Learning 6.7960.2x | Learning rate, momentum and local minima |
| [Robot Theatre](https://codey-m.github.io/ai-arcade/robot-theatre.html) | CV+NLP 6.4600.1x | Bag-of-words features, word order and bigrams |
| [Pairing Bench](https://codey-m.github.io/ai-arcade/pairing-bench.html) | Probability+SDA 6.3710.3x | Covariance: pairing changes the spread of a sum |
| [Lookout Tower](https://codey-m.github.io/ai-arcade/lookout-tower.html) | Deep Learning 6.7960.3x | Convolution, stride and the receptive field |
| [Tipping Point](https://codey-m.github.io/ai-arcade/mean-flights.html) | Probability+SDA 6.3710.4x | Sample means and the central limit theorem |
| [Photo Finish](https://codey-m.github.io/ai-arcade/photo-finish.html) | Deep Learning 6.7960.2x | Accuracy, precision and recall with a rare class |
| [Crossfade](https://codey-m.github.io/ai-arcade/crossfade.html) | CV+NLP 6.4600.5x | Combining camera and microphone estimates with hard gates |
| [Echo Dancer](https://codey-m.github.io/ai-arcade/echo-the-dance.html) | Deep Learning 6.7960.4x | Principal component analysis |
| [Wonder Fold](https://codey-m.github.io/ai-arcade/the-wonder-fold.html) | Probability+SDA 6.3710.5x | Sample size and the power of a test |
| [Next Note](https://codey-m.github.io/ai-arcade/next-note.html) | Deep Learning 6.7960.5x | Generating one piece at a time: temperature and top-k sampling |
| [Stunt School](https://codey-m.github.io/ai-arcade/stunt-school.html) | CV+NLP 6.4600.5x | Reward, exploration and a learned policy |
| [Wish List](https://codey-m.github.io/ai-arcade/workshop-brief.html) | AI Systems+Agents 6.S978.2x | Instructions and examples: what a brief must say |

## Demo tips

- Every game is one self-contained HTML file. It runs offline, stores nothing and makes no network requests, so a downloaded copy works too.
- Add `?embed=1` to hide arcade navigation. Course exports also use `data-mode="course"`; `?mode=course` previews their gated explanations and course behavior.
- Add `?seed=` with a number to open a specific round, for example `photo-finish.html?seed=7`. Without it, each game opens on its introductory round. The address bar always holds the round you are on, so copying it shares that round.

## How this repository works

The games are developed and tested in the `ai-arcade-review/pilots` working folder, not here. This repository holds the playable site and the scripts that assemble it.

- `site/` is the published site: the launcher (`index.html`), one HTML file per game and the card thumbnails.
- `games.json` lists the games in launcher order: title, card text, course, colour, and which built file in the pilots folder each one comes from.
- `launcher.html` is the launcher template.
- `sync.py` copies the built games into `site/`, removes review-only links (build notes and archived course originals) and writes `site/index.html`. It stops if any other link would leave the site.
- `tools/thumbs.py` redraws the thumbnails (macOS with Google Chrome). It hides all text first, because course images carry no words; each card's alt text describes the scene.
- An optional `thumb_asset` uses a self-contained, text-free SVG in the pilots folder instead of capturing the game. Transfer Desk uses this path because its play area is a text terminal. The SVG must have a 16:10 viewBox; scripts, text, embedded images and external resources are rejected.
- `.github/workflows/pages.yml` publishes `site/` to GitHub Pages on every push to `main` that changes `site/`. You can also run it by hand from the Actions tab.

## Updating the site

Build each changed game with its own builder. For Wish List, from this repository:

```sh
python3 ../ai-arcade-review/pilots/workshop-brief/build.py
python3 sync.py
python3 tools/thumbs.py workshop-brief
python3 sync.py
```

Review the generated site and thumbnails before committing and pushing. Course hosting is separate. Course-mode copies come from `ai-arcade-review/pilots/wire_course.py`, and each course hosts its own: for CV+NLP, `CV_NLP/docs/publish_widgets.py` mirrors them to `CV_NLP_Labs/widgets/`, and the course imports wait until those hosted copies are live. Wish List is not wired into a course yet.

A game marked `"hold": true` in `games.json` keeps its place in the order but stays off the site and is skipped by thumbnail generation. No games are currently held. To add a game, add an entry with its built file name and the CSS selector of its play area. Optional fields shape the thumbnail (every captured scene is shown whole, padded to 16:10 on white): `thumb_steps` plays the game into a more telling state first (selectors to click, `{"set": selector, "value": v}` for a slider, or `{"key": selector, "press": key, "times": n}` for keyboard controls), and `thumb_query` opens a particular round (for example `seed=4`). `thumb_live` (`{"steps": [...], "after": ms}`) then plays on in real time and catches the scene mid-animation, through Chrome's DevTools protocol (`tools/live.py`, standard library only). A `thumb_asset` uses the illustrated-asset path instead. Refresh the launcher with `sync.py` after producing a thumbnail so its image fingerprint is current.
