# news-image-20nov

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Gobpox/news-image-20nov/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Gobpox/news-image-20nov/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

One 1024×1024 newspaper front page that sums up the world's news of Friday 20 November 2026: 46 stories — 4 illustrated heroes (Russia's missile blitz on Kyiv's bridges, Cyclone Akvan's Odisha landfall, COP31's deadlocked final day, Asia's AI sell-off), 12 illustrated cards with layered scenes drawn by a reusable Pillow scene library (`draw.py`: gradients, soft shadows, halftone and paper texture, in-scene labels), a big-number tally strip, a UTC timeline, a region tally bar, a status chip and source on every hero and card, a dotted world map with numbered pins, and 30 one-line briefs — including the evening results early editions missed (the Wall Street close and GTA VI's first-day sales). Every letter is rendered by code; no AI-generated text appears in the image. A date-check box names the stories deliberately left out because they were not 20 November news.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` copies the pre-rendered `entry.png` (drawn by `draw.py`) to the output directory, byte for byte, deterministically.

---

<sub>Entered on [make.fun](https://make.fun/?ref=ab6123w1&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>

## Typography

Bundled under the SIL Open Font License (texts in `fonts/`): Playfair
Display (masthead and headlines) and Archivo (labels, kickers and
statistics). `draw.py` loads them from the repo — no system fonts needed.
