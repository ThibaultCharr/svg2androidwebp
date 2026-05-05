"""SVG to Android WebP converter — pure conversion logic, no UI dependency."""
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

# Ensure Homebrew paths are visible when launched from Spotlight/Finder
for _p in ("/opt/homebrew/bin", "/usr/local/bin"):
    if _p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _p + ":" + os.environ.get("PATH", "")

# Density scale factors relative to mdpi (1x baseline)
DENSITY_SCALES = {
    "mdpi":    1.0,
    "hdpi":    1.5,
    "xhdpi":   2.0,
    "xxhdpi":  3.0,
    "xxxhdpi": 4.0,
}

BASELINES = ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]


def check_dependencies():
    """Returns a list of missing tool names, empty if all present."""
    missing = []
    if not shutil.which("rsvg-convert"):
        missing.append("librsvg")
    if not shutil.which("cwebp"):
        missing.append("webp")
    return missing


def detect_dimensions(svg_path):
    """
    Returns (width, height) as ints from the SVG file.
    Reads width/height attributes first, falls back to viewBox.
    Raises ValueError if dimensions cannot be detected.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    width_str = root.get("width", "")
    height_str = root.get("height", "")

    if not width_str.endswith("%") and not height_str.endswith("%"):
        try:
            w = int(float(re.sub(r"[a-zA-Z]", "", width_str)))
            h = int(float(re.sub(r"[a-zA-Z]", "", height_str)))
            if w > 0 and h > 0:
                return w, h
        except ValueError:
            pass

    # Fallback to viewBox="0 0 W H"
    viewbox = root.get("viewBox", "")
    parts = viewbox.strip().split()
    if len(parts) == 4:
        try:
            w, h = int(float(parts[2])), int(float(parts[3]))
            if w > 0 and h > 0:
                return w, h
        except ValueError:
            pass

    raise ValueError("Could not detect SVG dimensions.")


def convert(svg_path, icon_name, module_path, width=None, height=None, baseline="mdpi"):
    """
    Converts svg_path to WebP for all 5 Android densities.
    width/height: source dimensions in px (detected from SVG if not provided).
    baseline: which density the source dimensions represent (default: hdpi).
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

    if not icon_name or os.sep in icon_name or (os.altsep and os.altsep in icon_name):
        raise RuntimeError(f"Error: invalid icon name: {icon_name!r}")
    if not re.match(r'^[a-z0-9_.]+$', icon_name):
        raise RuntimeError(
            f"Error: invalid icon name {icon_name!r}. "
            "Use only lowercase letters, digits, underscores, and dots."
        )

    if width is None or height is None:
        try:
            width, height = detect_dimensions(svg_path)
        except ValueError as e:
            raise RuntimeError(str(e))

    if baseline not in DENSITY_SCALES:
        raise RuntimeError(f"Error: unknown baseline density: {baseline!r}")

    baseline_scale = DENSITY_SCALES[baseline]
    res_dir = os.path.join(module_path, "src", "main", "res")

    for density, scale in DENSITY_SCALES.items():
        w = max(1, round(width * scale / baseline_scale))
        h = max(1, round(height * scale / baseline_scale))
        out_dir = os.path.join(res_dir, f"drawable-{density}")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{icon_name}.webp")

        rsvg = subprocess.run(
            ["rsvg-convert", "-w", str(w), "-h", str(h), svg_path],
            capture_output=True,
        )
        if rsvg.returncode != 0:
            raise RuntimeError(rsvg.stderr.decode().strip() or f"rsvg-convert failed (exit {rsvg.returncode})")

        cwebp = subprocess.run(
            ["cwebp", "-lossless", "-o", out_path, "--", "-"],
            input=rsvg.stdout,
            capture_output=True,
        )
        if cwebp.returncode != 0:
            raise RuntimeError(cwebp.stderr.decode().strip() or f"cwebp failed (exit {cwebp.returncode})")

    return f"Done! All densities generated for '{icon_name}'."


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Convert an SVG to Android WebP density variants."
    )
    parser.add_argument("svg", help="Path to the source SVG file")
    parser.add_argument("icon_name", help="Android resource name (e.g. ic_home_euro_coin)")
    parser.add_argument("module_path", help="Android module root (e.g. libraries/MyModule/impl)")
    parser.add_argument("--width", type=int, default=None, help="Override source width in px")
    parser.add_argument("--height", type=int, default=None, help="Override source height in px")
    parser.add_argument(
        "--baseline",
        choices=BASELINES,
        default="mdpi",
        help="Density the source dimensions represent (default: mdpi)",
    )
    args = parser.parse_args()
    try:
        msg = convert(
            args.svg, args.icon_name, args.module_path,
            width=args.width, height=args.height, baseline=args.baseline,
        )
        print(msg)
    except RuntimeError as e:
        print(e)
        import sys; sys.exit(1)
