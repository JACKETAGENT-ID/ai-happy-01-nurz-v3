# nurz — ai-happy-01 entry

**Concept:** The rematch nobody expected. A joyful old tortoise — eyes
shut, grinning ear to ear, tiny gold party hat on his head — cruises past
three completely baffled hares on a bright red skateboard, in warm sunset
light over rolling hills. Storybook illustration, big clear shapes, one
instant joke: slow and steady didn't just win the race, he upgraded.

No text in the image, nothing stock — just pure, specific glee that still
reads clearly at thumbnail size.

## How it works

The artwork is bundled as `image.png` (1024×1024 PNG). `main.py` validates
it (PNG signature, IHDR dimensions, chunk skeleton, competition size
limits) and copies it byte-for-byte to the output, so repeated runs are
perfectly deterministic.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

Python 3.13, standard library only.
