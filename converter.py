"""SVG to Android WebP converter — pure conversion logic, no UI dependency."""
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

DENSITIES = [
    ("mdpi",     2, 3),
    ("hdpi",     1, 1),
    ("xhdpi",    4, 3),
    ("xxhdpi",   2, 1),
    ("xxxhdpi",  8, 3),
]


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

    if not icon_name or os.sep in icon_name or (os.altsep and os.altsep in icon_name):
        raise RuntimeError(f"Error: invalid icon name: {icon_name!r}")

    try:
        width, height = detect_dimensions(svg_path)
    except ValueError as e:
        raise RuntimeError(str(e))

    res_dir = os.path.join(module_path, "src", "main", "res")

    for density, num, den in DENSITIES:
        w = max(1, width * num // den)
        h = max(1, height * num // den)
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
