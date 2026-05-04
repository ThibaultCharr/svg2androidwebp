# svg2androidwebp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS menubar app in Python that converts an SVG file into WebP images for all 5 Android density buckets.

**Architecture:** `converter.py` is a pure Python module that ports the existing shell script logic — it detects SVG dimensions and calls `rsvg-convert` + `cwebp` as subprocesses. `app.py` owns the `rumps` menubar lifecycle and a `tkinter` conversion window, calling `converter.py` in a background thread.

**Tech Stack:** Python 3, `rumps` (menubar), `tkinter` (UI), `xml.etree.ElementTree` (SVG parsing), `subprocess` (rsvg-convert/cwebp), `threading` (background conversion)

---

## File Map

| File | Responsibility |
|---|---|
| `converter.py` | SVG dimension detection, dependency checking, subprocess calls, density output |
| `app.py` | rumps app, menubar menu, tkinter window, background thread wiring |
| `requirements.txt` | pip dependencies (rumps only) |

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `converter.py` (empty stub)
- Create: `app.py` (empty stub)

- [ ] **Step 1: Create `requirements.txt`**

```
rumps
```

- [ ] **Step 2: Create empty `converter.py` stub**

```python
# SVG to Android WebP converter
```

- [ ] **Step 3: Create empty `app.py` stub**

```python
# svg2androidwebp menubar app
```

- [ ] **Step 4: Install dependencies**

```bash
pip install rumps
```

Expected output: `Successfully installed rumps-x.x.x` (or already satisfied)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt converter.py app.py
git commit -m "chore: scaffold project files"
```

---

### Task 2: Implement `converter.py` — dependency check

**Files:**
- Modify: `converter.py`

- [ ] **Step 1: Implement `check_dependencies()` in `converter.py`**

```python
import shutil

def check_dependencies():
    """Returns a list of missing tool names, empty if all present."""
    missing = []
    if not shutil.which("rsvg-convert"):
        missing.append("librsvg")
    if not shutil.which("cwebp"):
        missing.append("webp")
    return missing
```

- [ ] **Step 2: Verify manually**

```bash
python3 -c "from converter import check_dependencies; print(check_dependencies())"
```

Expected: `[]` if both tools are installed, or e.g. `['librsvg']` if missing.

- [ ] **Step 3: Commit**

```bash
git add converter.py
git commit -m "feat: add dependency check to converter"
```

---

### Task 3: Implement `converter.py` — SVG dimension detection

**Files:**
- Modify: `converter.py`

- [ ] **Step 1: Add `detect_dimensions()` to `converter.py`**

```python
import xml.etree.ElementTree as ET

def detect_dimensions(svg_path):
    """
    Returns (width, height) as ints from the SVG file.
    Reads width/height attributes first, falls back to viewBox.
    Raises ValueError if dimensions cannot be detected.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Strip namespace if present: {http://www.w3.org/2000/svg}svg -> svg
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    width = root.get("width", "")
    height = root.get("height", "")

    # Strip non-numeric characters (e.g. "24px" -> "24")
    import re
    width = re.sub(r"[^0-9]", "", width)
    height = re.sub(r"[^0-9]", "", height)

    if width and height and width != "0" and height != "0":
        return int(width), int(height)

    # Fallback to viewBox="0 0 W H"
    viewbox = root.get("viewBox", "")
    parts = viewbox.strip().split()
    if len(parts) == 4:
        try:
            return int(float(parts[2])), int(float(parts[3]))
        except ValueError:
            pass

    raise ValueError("Could not detect SVG dimensions.")
```

- [ ] **Step 2: Verify manually with a real SVG**

Create a minimal test SVG at `/tmp/test.svg`:
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"></svg>
```

Then run:
```bash
python3 -c "from converter import detect_dimensions; print(detect_dimensions('/tmp/test.svg'))"
```

Expected: `(48, 48)`

- [ ] **Step 3: Commit**

```bash
git add converter.py
git commit -m "feat: add SVG dimension detection to converter"
```

---

### Task 4: Implement `converter.py` — density conversion

**Files:**
- Modify: `converter.py`

- [ ] **Step 1: Add `convert()` to `converter.py`**

```python
import os
import subprocess

DENSITIES = [
    ("mdpi",     2, 3),
    ("hdpi",     1, 1),
    ("xhdpi",    4, 3),
    ("xxhdpi",   2, 1),
    ("xxxhdpi",  8, 3),
]

def convert(svg_path, icon_name, module_path):
    """
    Converts svg_path to WebP for all 5 Android densities.
    SVG dimensions treated as hdpi (1.5x) baseline.
    Raises RuntimeError on any failure.
    """
    missing = check_dependencies()
    if missing:
        raise RuntimeError(
            f"Error: missing required tools: {' '.join(missing)}\n"
            f"Install with: brew install {' '.join(missing)}"
        )

    if not os.path.isfile(svg_path):
        raise RuntimeError(f"Error: SVG file not found: {svg_path}")

    if not os.path.isdir(module_path):
        raise RuntimeError(f"Error: Module path not found: {module_path}")

    width, height = detect_dimensions(svg_path)

    res_dir = os.path.join(module_path, "src", "main", "res")

    for density, num, den in DENSITIES:
        w = width * num // den
        h = height * num // den
        out_dir = os.path.join(res_dir, f"drawable-{density}")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{icon_name}.webp")

        rsvg = subprocess.run(
            ["rsvg-convert", "-w", str(w), "-h", str(h), svg_path],
            capture_output=True,
        )
        if rsvg.returncode != 0:
            raise RuntimeError(rsvg.stderr.decode().strip())

        cwebp = subprocess.run(
            ["cwebp", "-lossless", "-o", out_path, "--", "-"],
            input=rsvg.stdout,
            capture_output=True,
        )
        if cwebp.returncode != 0:
            raise RuntimeError(cwebp.stderr.decode().strip())

    return f"Done! All densities generated for '{icon_name}'."
```

- [ ] **Step 2: Add CLI entry point at bottom of `converter.py`**

```python
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python3 converter.py <input.svg> <icon_name> <module_path>")
        sys.exit(1)
    try:
        msg = convert(sys.argv[1], sys.argv[2], sys.argv[3])
        print(msg)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
```

- [ ] **Step 3: Verify manually with a real SVG and a real Android module path**

```bash
python3 converter.py /tmp/test.svg test_icon /path/to/your/android/module
```

Expected: Output listing each density and `Done! All densities generated for 'test_icon'.`

Check output files exist:
```bash
ls /path/to/your/android/module/src/main/res/drawable-*/test_icon.webp
```

- [ ] **Step 4: Commit**

```bash
git add converter.py
git commit -m "feat: implement full density conversion in converter"
```

---

### Task 5: Implement `app.py` — rumps menubar skeleton

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Implement the rumps app class in `app.py`**

```python
import rumps
import threading
import tkinter as tk

class SVG2AndroidWebPApp(rumps.App):
    def __init__(self):
        super().__init__("SVG→WebP", quit_button=None)
        self.menu = [
            rumps.MenuItem("Convert SVG...", callback=self.open_window),
            None,  # separator
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self._window = None

    @rumps.clicked("Convert SVG...")
    def open_window(self, _):
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return
        self._launch_window()

    def _launch_window(self):
        t = threading.Thread(target=self._run_window, daemon=True)
        t.start()

    def _run_window(self):
        root = tk.Tk()
        root.withdraw()  # hide root window
        self._window = ConversionWindow(root)
        root.mainloop()


if __name__ == "__main__":
    SVG2AndroidWebPApp().run()
```

- [ ] **Step 2: Verify the app launches and shows a menubar icon**

```bash
python3 app.py
```

Expected: A "SVG→WebP" text appears in the menubar. Clicking it shows "Convert SVG..." and "Quit". Quit exits cleanly. (The window won't open yet — `ConversionWindow` is not defined.)

Stop with Ctrl+C or via Quit menu item.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add rumps menubar skeleton"
```

---

### Task 6: Implement `app.py` — tkinter conversion window

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add `ConversionWindow` class to `app.py`, above `SVG2AndroidWebPApp`**

```python
import tkinter as tk
from tkinter import filedialog

class ConversionWindow:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.title("SVG to Android WebP")
        self.win.resizable(True, True)
        self.win.minsize(500, 260)

        pad = {"padx": 10, "pady": 6}

        # SVG File row
        tk.Label(self.win, text="SVG File:").grid(row=0, column=0, sticky="e", **pad)
        self.svg_var = tk.StringVar()
        self.svg_entry = tk.Entry(self.win, textvariable=self.svg_var, state="readonly", width=45)
        self.svg_entry.grid(row=0, column=1, sticky="ew", **pad)
        tk.Button(self.win, text="Browse...", command=self._browse_svg).grid(row=0, column=2, **pad)

        # Icon Name row
        tk.Label(self.win, text="Icon Name:").grid(row=1, column=0, sticky="e", **pad)
        self.name_var = tk.StringVar()
        self.name_var.trace_add("write", self._on_field_change)
        tk.Entry(self.win, textvariable=self.name_var, width=45).grid(row=1, column=1, sticky="ew", **pad)

        # Module Path row
        tk.Label(self.win, text="Module Path:").grid(row=2, column=0, sticky="e", **pad)
        self.module_var = tk.StringVar()
        self.module_entry = tk.Entry(self.win, textvariable=self.module_var, state="readonly", width=45)
        self.module_entry.grid(row=2, column=1, sticky="ew", **pad)
        tk.Button(self.win, text="Browse...", command=self._browse_module).grid(row=2, column=2, **pad)

        # Convert button
        self.convert_btn = tk.Button(self.win, text="Convert", command=self._on_convert, state="disabled")
        self.convert_btn.grid(row=3, column=1, sticky="w", **pad)

        # Result label
        self.result_var = tk.StringVar()
        self.result_label = tk.Label(self.win, textvariable=self.result_var, wraplength=460, justify="left")
        self.result_label.grid(row=4, column=0, columnspan=3, sticky="w", **pad)

        # "Convert another" button (hidden initially)
        self.reset_btn = tk.Button(self.win, text="Convert another", command=self._reset)
        self.reset_btn.grid(row=5, column=1, sticky="w", **pad)
        self.reset_btn.grid_remove()

        self.win.columnconfigure(1, weight=1)
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        self.win.lift()
        self.win.focus_force()

    def _browse_svg(self):
        path = filedialog.askopenfilename(
            title="Select SVG file",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
        )
        if path:
            self.svg_var.set(path)
            self._on_field_change()

    def _browse_module(self):
        path = filedialog.askdirectory(title="Select Android module directory")
        if path:
            self.module_var.set(path)
            self._on_field_change()

    def _on_field_change(self, *_):
        if self.svg_var.get() and self.name_var.get().strip() and self.module_var.get():
            self.convert_btn.config(state="normal")
        else:
            self.convert_btn.config(state="disabled")

    def _on_convert(self):
        self.convert_btn.config(state="disabled")
        self.reset_btn.grid_remove()
        self.result_var.set("Converting...")

        svg = self.svg_var.get()
        name = self.name_var.get().strip()
        module = self.module_var.get()

        def run():
            from converter import convert
            try:
                msg = convert(svg, name, module)
                self.win.after(0, self._on_success, msg)
            except RuntimeError as e:
                self.win.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_success(self, msg):
        self.result_var.set(msg)
        self.reset_btn.grid()

    def _on_error(self, msg):
        self.result_var.set(msg)
        self.convert_btn.config(state="normal")

    def _reset(self):
        self.svg_var.set("")
        self.name_var.set("")
        self.module_var.set("")
        self.result_var.set("")
        self.reset_btn.grid_remove()
        self.convert_btn.config(state="disabled")

    def winfo_exists(self):
        try:
            return self.win.winfo_exists()
        except Exception:
            return False

    def lift(self):
        self.win.lift()

    def focus_force(self):
        self.win.focus_force()
```

- [ ] **Step 2: Run the app and test the full flow**

```bash
python3 app.py
```

Test checklist:
1. Click "Convert SVG..." — window opens
2. Click "Convert SVG..." again — window comes to front (not a second window)
3. Browse for an SVG — path appears in field
4. Type an icon name — Convert button enables
5. Browse for a module path — all 3 fields filled
6. Click Convert — shows "Converting...", then success message
7. Click "Convert another" — all fields reset
8. Click Convert with missing deps (if you want to test) — shows error message with brew instructions
9. Close window, click "Convert SVG..." — new window opens

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: implement tkinter conversion window"
```

---

### Task 7: Final polish — window re-open fix and README

**Files:**
- Modify: `app.py`
- Create: `README.md`

- [ ] **Step 1: Fix window re-open after it's been closed**

The current `open_window` checks `winfo_exists()`. When the window is closed, `self._window` still holds a reference to the destroyed `ConversionWindow`. Update `SVG2AndroidWebPApp._launch_window` to clear `self._window` when the window is closed:

In `ConversionWindow.__init__`, replace:
```python
self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
```
with:
```python
self.win.protocol("WM_DELETE_WINDOW", self._on_close)
```

Add `_on_close` method to `ConversionWindow`:
```python
def _on_close(self):
    self.win.destroy()
```

Update `SVG2AndroidWebPApp._run_window` to clear `self._window` after mainloop exits:
```python
def _run_window(self):
    root = tk.Tk()
    root.withdraw()
    self._window = ConversionWindow(root)
    root.mainloop()
    self._window = None
```

- [ ] **Step 2: Verify close + reopen works**

```bash
python3 app.py
```

1. Open window via menu
2. Close the window with the red X
3. Click "Convert SVG..." again — a fresh window should open (not crash)

- [ ] **Step 3: Create `README.md`**

```markdown
# svg2androidwebp

macOS menubar app that converts an SVG file into WebP images for all 5 Android density buckets (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi).

## Requirements

- Python 3
- `brew install librsvg webp`
- `pip install rumps`

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
```

- [ ] **Step 4: Commit**

```bash
git add app.py README.md
git commit -m "fix: clear window reference on close; add README"
```

---

### Task 8: Push to GitHub

- [ ] **Step 1: Verify git remote is set correctly**

```bash
git remote -v
```

Expected: shows `origin https://<PAT>@github.com/<username>/svg2androidwebp.git`

- [ ] **Step 2: Push**

```bash
git push -u origin main
```

- [ ] **Step 3: Verify on GitHub**

Open `https://github.com/<username>/svg2androidwebp` in a browser and confirm all commits are present.
