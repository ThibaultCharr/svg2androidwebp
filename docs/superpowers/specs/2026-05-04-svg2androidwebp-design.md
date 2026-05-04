# svg2androidwebp — Design Spec

**Date:** 2026-05-04

## Overview

A macOS-only menubar app (no dock icon) that converts an SVG file into a set of WebP images for all 5 Android density buckets (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi). The app is fully Python, using `rumps` for the menubar and `tkinter` for the conversion window.

---

## Architecture

Three files:

```
svg2androidwebp/
├── app.py              # rumps menubar app + tkinter window
├── converter.py        # conversion logic (Python port of existing shell script)
└── requirements.txt    # rumps only
```

- `app.py` owns the menubar lifecycle: creates the `NSStatusItem`, handles menu items ("Convert SVG...", "Quit"), and opens/raises the tkinter window.
- `converter.py` is a pure Python module with no UI dependency. It replicates the existing shell script logic: detects SVG dimensions, calls `rsvg-convert` and `cwebp` as subprocesses, and writes output under `<module_path>/src/main/res/drawable-<density>/`.
- `app.py` imports and calls `converter.py` in a background thread.

---

## Menubar Behavior

- App launches with no dock icon (`LSUIElement = YES` equivalent via `rumps`).
- Menubar icon is a simple icon (or text fallback).
- Clicking the menubar icon shows a dropdown menu with:
  - **Convert SVG...** — opens the conversion window
  - **Quit** — exits the app

---

## Conversion Window UI

A standard resizable `tkinter.Toplevel` window. Stays open after conversion. If already open and the user clicks "Convert SVG..." again, the window is brought to front.

Fields (top to bottom):

| Field | Type | Behavior |
|---|---|---|
| SVG File | Read-only text + Browse button | `filedialog.askopenfilename` filtered to `.svg` |
| Icon Name | Editable text entry | User types manually |
| Module Path | Read-only text + Browse button | `filedialog.askdirectory` |
| Convert | Button | Disabled until all 3 fields are non-empty |
| Result | Label | Shows status: converting / success / error |

On success:
- Result label shows: `Done! All densities generated for '<icon_name>'.`
- A **Convert another** button appears, which resets all fields and the result label.

---

## Data Flow

1. User clicks "Convert SVG..." in the menubar menu.
2. `app.py` opens or raises the tkinter window.
3. User fills SVG file, icon name, module path — Convert button enables when all 3 are non-empty.
4. User clicks Convert — button disables, result label shows "Converting...".
5. `converter.py` runs in a background thread:
   - Checks `rsvg-convert` and `cwebp` on `$PATH`.
   - Reads SVG width/height from `width`/`height` attributes or `viewBox` fallback.
   - Calls `rsvg-convert` + `cwebp` for each of the 5 density folders.
6. On completion, main thread updates result label (success or error).
7. On success, "Convert another" button appears to reset the form.

---

## Density Scale

SVG dimensions are treated as hdpi (1.5x) baseline:

| Density | Scale factor |
|---|---|
| mdpi | 2/3 |
| hdpi | 1 |
| xhdpi | 4/3 |
| xxhdpi | 2 |
| xxxhdpi | 8/3 |

Output path: `<module_path>/src/main/res/drawable-<density>/<icon_name>.webp`

---

## Error Handling

All errors leave fields intact and re-enable the Convert button so the user can correct and retry.

| Condition | Message shown |
|---|---|
| `rsvg-convert` or `cwebp` missing | "Error: missing required tools: librsvg webp\nInstall with: brew install librsvg webp" |
| SVG file not found | "Error: SVG file not found: \<path\>" |
| Cannot detect SVG dimensions | "Error: Could not detect SVG dimensions." |
| Module path not found | "Error: Module path not found: \<path\>" |
| Subprocess failure | Stderr output from the failed command |

---

## Dependencies

- `rumps` — install via `pip install rumps`
- `rsvg-convert` — install via `brew install librsvg`
- `cwebp` — install via `brew install webp`
- `tkinter` — bundled with macOS Python, no install needed

---

## Testing

No automated tests. `converter.py` is a standalone callable module and can be tested directly:

```bash
python3 converter.py <input.svg> <icon_name> <module_path>
```

---

## Running Locally

```bash
pip install rumps
python3 app.py
```

---

## Distribution (Optional, Later)

`py2app` can bundle the app into a standalone `.app` for `/Applications`. Not required for personal use.
