"""SVG to Android WebP converter — pure conversion logic, no UI dependency."""
import re
import shutil
import xml.etree.ElementTree as ET


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
