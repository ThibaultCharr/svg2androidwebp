<table border="0" cellspacing="0" cellpadding="0"><tr>
<td><picture><source media="(prefers-color-scheme: dark)" srcset="icon_dark.png"><img src="icon.png" width="128" alt="SVG2AndroidWebP"></picture></td>
<td><h1>&nbsp;SVG2AndroidWebP</h1></td>
</tr></table>

A macOS tool that takes a single SVG file and converts it into WebP images for all 5 Android density buckets — mdpi, hdpi, xhdpi, xxhdpi, and xxxhdpi — in one go. It reads the dimensions directly from the SVG, scales them proportionally for each density, and writes the output files into the correct `drawable-<density>` folders inside your Android module.

It comes in two forms: a native macOS wizard app you can launch from Spotlight, and a command-line tool installable via Homebrew.

## GUI App — Homebrew (recommended)

```bash
brew tap ThibaultCharr/svg2androidwebp
brew install --cask svg2androidwebp
```

The app is fully self-contained — no external tools required.

Alternatively, download `SVG2AndroidWebP.zip` from the [Releases](https://github.com/ThibaultCharr/svg2androidwebp/releases) page, unzip, and move to `/Applications`.

> First launch: right-click → Open to bypass Gatekeeper (the app is not signed with an Apple Developer certificate).

## CLI — Homebrew (recommended)

```bash
brew tap ThibaultCharr/svg2androidwebp
brew install svg2androidwebp
```

Then use it as:

```bash
svg2androidwebp <input.svg> <icon_name> <module_path> [options]
```

## CLI — Manual

Clone the repo and run `converter.py` directly. Either `pip install cairosvg Pillow` or `brew install librsvg webp` must be available.

```bash
python3 converter.py <input.svg> <icon_name> <module_path> [options]
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--width W` | from SVG | Override source width in px |
| `--height H` | from SVG | Override source height in px |
| `--baseline DENSITY` | `mdpi` | Density the source dimensions represent |

`--baseline` accepts: `mdpi`, `hdpi`, `xhdpi`, `xxhdpi`, `xxxhdpi`

## Examples

```bash
# Read dimensions from SVG, mdpi baseline
svg2androidwebp icon.svg ic_home libraries/Home/impl

# Custom dimensions, xhdpi baseline
svg2androidwebp icon.svg ic_home libraries/Home/impl --width 64 --height 64 --baseline xhdpi
```

## Output

Files are written to:

```
<module_path>/src/main/res/drawable-<density>/<icon_name>.webp
```

The source dimensions are treated as the chosen baseline density and scaled proportionally:

| Density | Scale |
|---|---|
| mdpi | 1× |
| hdpi | 1.5× |
| xhdpi | 2× |
| xxhdpi | 3× |
| xxxhdpi | 4× |
