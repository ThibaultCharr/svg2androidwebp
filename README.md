# svg2androidwebp

macOS menubar app that converts an SVG file into WebP images for all 5 Android density buckets (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi).

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
python3 converter.py input.svg icon_name path/to/android/module
```

## Density scale

SVG dimensions are treated as hdpi (1.5x) baseline. Output is written to `<module>/src/main/res/drawable-<density>/<icon_name>.webp`.
