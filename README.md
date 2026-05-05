<p align="center">
  <img src="icon.png" width="128" alt="svg2androidwebp">
</p>

# svg2androidwebp

macOS app that converts an SVG file into WebP images for all 5 Android density buckets (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi). Runs as a native 3-step wizard and can be launched via Spotlight.

## Requirements

- Python 3.7+
- `brew install librsvg webp`
- `pip install -r requirements.txt`

## Run directly

```bash
.venv/bin/python3 app.py
```

A 3-step wizard opens: pick an SVG file → enter the icon name → choose the Android module folder.

## Build a Spotlight-launchable .app

```bash
pip install py2app
.venv/bin/python3 setup.py py2app
# App is at dist/svg2androidwebp.app — move to /Applications for Spotlight
open dist/svg2androidwebp.app
```

## Manual conversion (no UI)

```bash
python3 converter.py input.svg icon_name path/to/android/module [--width W] [--height H] [--baseline DENSITY]
```

- `--width` / `--height` — override source dimensions in px (default: read from SVG)
- `--baseline` — density the source dimensions represent: `mdpi`, `hdpi`, `xhdpi`, `xxhdpi`, `xxxhdpi` (default: `hdpi`)

Examples:
```bash
# Use SVG dimensions, hdpi baseline (default)
python3 converter.py icon.svg ic_home libraries/Home/impl

# Custom size, xhdpi baseline
python3 converter.py icon.svg ic_home libraries/Home/impl --width 64 --height 64 --baseline xhdpi
```

## Density scale

SVG dimensions are treated as hdpi (1.5x) baseline. Output is written to `<module>/src/main/res/drawable-<density>/<icon_name>.webp`.
