# AI Arcade

Sixteen short games built from MIT course activities, prototyped for MIT Learn. Each game opens with a goal, plays out as you move things, and keeps its explanation in a closed drop-down.

**Play:** https://codey-m.github.io/ai-arcade/

Games appear in play order, not course order: the subjects alternate, each statistics puzzle comes before the game that applies it (Beach Beeps before Photo Finish, Tipping Point before Wonder Fold), and each course's games otherwise keep their course order.

| Game | Course | Idea |
| --- | --- | --- |
| [Beach Beeps](https://codey-m.github.io/ai-arcade/beach-beeps.html) | Probability+SDA 6.3710.1x | Bayes' rule and the base rate |
| [Recycling Day](https://codey-m.github.io/ai-arcade/sort-the-recycling.html) | Deep Learning 6.7960.1x | Model capacity: building and training a small network |
| [Backup Power](https://codey-m.github.io/ai-arcade/backup-power.html) | Probability+SDA 6.3710.1x | Independence and reliability |
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
- `.github/workflows/pages.yml` publishes `site/` to GitHub Pages on every push to `main` that changes `site/`. You can also run it by hand from the Actions tab.

## Updating the site

Build each changed game with its own builder. For the Module 5 additions, from this repository:

```sh
python3 ../ai-arcade-review/pilots/crossfade/build.py
python3 ../ai-arcade-review/pilots/stunt-school/build.py
python3 sync.py
python3 tools/thumbs.py crossfade stunt-school
python3 sync.py
```

Review the generated site and thumbnails before committing and pushing. Crossfade and Stunt School are registered locally; the current handoff has not run the site sync or published them. Course hosting is separate: `CV_NLP/docs/publish_widgets.py` mirrors their generated course-mode copies to `CV_NLP_Labs/widgets/`. The overview iframes point to that course host, and the course imports wait until those hosted copies are live.

A game marked `"hold": true` in `games.json` keeps its place in the order but stays off the site (none at the moment). To add a game, add an entry to `games.json` with its built file name and the CSS selector of its play area (used for the thumbnail), then run step 2. Optional fields shape the thumbnail (every scene is shown whole, padded to 16:10 on white): `thumb_steps` plays the game into a more telling state first (selectors to click, `{"set": selector, "value": v}` for a slider, or `{"key": selector, "press": key, "times": n}` for keyboard controls), and `thumb_query` opens a particular round (for example `seed=4`). `thumb_live` (`{"steps": [...], "after": ms}`) then plays on in real time and catches the scene mid-animation, through Chrome's DevTools protocol (`tools/live.py`, standard library only): planes in flight in Wonder Fold, crates in the air in Tipping Point.
