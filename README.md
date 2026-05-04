# svg2androidwebp

macOS menubar app that converts an SVG file into WebP images for all 5 Android density buckets (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi).

## Requirements

- Python 3
- `brew install librsvg webp`
- `pip install -r requirements.txt`

## Run

```bash
python3 app.py
```

## Manual conversion (no UI)

```bash
python3 converter.py input.svg icon_name path/to/android/module
```

## Density scale

SVG dimensions are treated as hdpi (1.5x) baseline. Output is written to `<module>/src/main/res/drawable-<density>/<icon_name>.webp`.
